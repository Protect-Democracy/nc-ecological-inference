# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "pyei==1.1.1",
#     "pymc==5.16.2",
# ]
# ///

# Standard libraries
import numpy as np
import pandas as pd

from pyei.r_by_c import RowByColumnEI

# Get number of registered voters per precinct
# Initialize an empty DataFrame to accumulate results
nc_registered_voters = pd.DataFrame(columns=["precinct_", "count"])

# Loop through chunks
filename = "VR_Snapshot_20241105.txt"
for chunk in pd.read_csv(
    filename,
    sep="	",
    encoding="utf-16",
    chunksize=100000,
    low_memory=False,
    on_bad_lines="warn",
):
    # Concatenate 'District' and 'SubDistrict' into 'district_'
    chunk = chunk.dropna(subset=["precinct_abbrv"])
    chunk = chunk[chunk["precinct_abbrv"].str.strip() != ""]

    chunk["precinct_"] = (
        chunk["county_desc"].astype(str) + " " + chunk["precinct_abbrv"].astype(str)
    )

    # Filter rows where 'Status' is 'Present' or 'Available'
    filtered_chunk = chunk[chunk["voter_status_desc"].isin(["ACTIVE", "INACTIVE"])]

    # Group by 'district_' and count occurrences
    chunk_counts = filtered_chunk.groupby("precinct_").size().reset_index(name="count")

    # Merge with cumulative results
    nc_registered_voters = (
        pd.concat([nc_registered_voters, chunk_counts])
        .groupby("precinct_")
        .sum()
        .reset_index()
    )


# Get election results per precinct
with open("NC_precinct_results_2024.txt", "r") as f:
    df = pd.read_csv(f, sep="	")
df["precinct_"] = df["County"] + " " + df["Precinct"]


def remove_zero_sum_precincts(df):
    precinct_sums = df.groupby("precinct_")["Total Votes"].transform("sum")
    return df[precinct_sums != 0]


df = remove_zero_sum_precincts(df)

prez = df[df["Contest Name"] == "US PRESIDENT"]

# In this analysis, we only care about Trump, Harris, "Other", and "No Vote"
candidates_of_interest_prez = ["Donald J. Trump", "Kamala D. Harris"]
prez["candidate"] = prez["Choice"].apply(
    lambda x: x if x in candidates_of_interest_prez else "Other"
)

prez = prez.groupby(["candidate", "precinct_"]).sum().reset_index()
votes_fractions_prez = prez.pivot(
    columns="precinct_", index="candidate", values="Total Votes"
)

# Figure out number of "No Vote"s by subtracting votes from registered voters
votes_fractions_prez = nc_registered_voters.merge(
    votes_fractions_prez.T, left_on="precinct_", right_index=True, how="inner"
)

votes_fractions_prez.index = votes_fractions_prez["precinct_"]
votes_fractions_prez["No Vote"] = (
    votes_fractions_prez["count"]
    - votes_fractions_prez["Donald J. Trump"]
    - votes_fractions_prez["Kamala D. Harris"]
    - votes_fractions_prez["Other"]
)
votes_fractions_prez = votes_fractions_prez[
    ["Donald J. Trump", "Kamala D. Harris", "Other", "No Vote"]
].T

precinct_pops = np.array(
    np.sum(votes_fractions_prez, axis=0).values, dtype=int
).flatten()

# Ecological inference needs vote share, not raw numbers of votes
prez_fractions = votes_fractions_prez / precinct_pops

# Get the number of votes for gubernatorial candidates
gov = df[df["Contest Name"] == "NC GOVERNOR"]

# In this analysis, we only care about Robinson, Stein, "Other", and "No Vote"
candidates_of_interest_gov = ["Josh Stein", "Mark Robinson"]
gov["candidate"] = gov["Choice"].apply(
    lambda x: x if x in candidates_of_interest_gov else "Other"
)

gov = gov.groupby(["candidate", "precinct_"]).sum().reset_index()
votes_fractions_gov = gov.pivot(
    columns="precinct_", index="candidate", values="Total Votes"
)

# Figure out number of "No Vote"s by subtracting votes from registered voters
votes_fractions_gov = nc_registered_voters.merge(
    votes_fractions_gov.T, left_on="precinct_", right_index=True, how="inner"
)

votes_fractions_gov.index = votes_fractions_gov["precinct_"]
votes_fractions_gov["No Vote"] = (
    votes_fractions_gov["count"]
    - votes_fractions_gov["Mark Robinson"]
    - votes_fractions_gov["Josh Stein"]
    - votes_fractions_gov["Other"]
)
votes_fractions_gov = votes_fractions_gov[
    ["Josh Stein", "Mark Robinson", "Other", "No Vote"]
].T

# Ecological inference needs vote share, not raw numbers of votes
gov_fractions = votes_fractions_gov / np.sum(votes_fractions_gov, axis=0)

mask = ~np.any(np.isnan(np.array(np.sum(votes_fractions_gov, axis=0), dtype=int)))

# Run the ecological inference
ei = RowByColumnEI(model_name="multinomial-dirichlet")

# Using some nondescriptive variables here to save space on screen
x = np.array(gov_fractions.values[:, mask].reshape(4,-1), dtype=float)
y = np.array(prez_fractions.values[:, mask].reshape(4, -1), dtype=float)
z = np.array(precinct_pops[mask].flatten(), dtype=int)
ei.fit(x,y,z,
       candidates_of_interest_gov + ['Other', 'No Vote'],
       candidates_of_interest_prez + ['Other', 'No Vote'],
       progressbar=True)


# Print results
means = pd.DataFrame(
    ei.posterior_mean_voting_prefs,
    columns=candidates_of_interest_prez + ["Other", "No Vote"],
    index=candidates_of_interest_gov + ["Other", "No Vote"],
)
print(means)
