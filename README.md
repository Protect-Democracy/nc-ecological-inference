# nc-ecological-inference

This repository contains the code and data to reproduce the ecological inference results presented in [*No, “Bullet Ballots” are Not Why Trump Won*](https://protdem.org/rolloffresponse).

## Instructions

To run the code, first clone this repository to the directory of your choice:
```{bash}
git clone https://github.com/Protect-Democracy/nc-ecological-inference.git # HTTP
git clone git@github.com:Protect-Democracy/nc-ecological-inference.git # SSH
```

To run the code, install `uv` to manage the isolated Python environment:

```{bash}
cd nc-ecological-inference
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You'll need to download the NC voter registration data:
```{bash}
curl -LsSf https://s3.amazonaws.com/dl.ncsbe.gov/data/Snapshots/VR_Snapshot_20241105.zip ./
```

Then unzip this file into the same working directory. Note that it is quite large (16 gigabytes or so).

Finally, run the code via Python:

```{bash}
uv run ei.py
```

Depending on your computer's speed, this may take some time. 

## Discussion

This script relies on [PyEI](https://github.com/mggg/ecological-inference/tree/main/pyei) for the number-crunching. 

We have vote tallies aggregated at the precinct level in North Carolina (from the link below), which includes votes for President and for Governor.
We also have voter registration data: in North Carolina, voters have to be registered ahead of Election Day.
That means we know exactly how many people voted, and how many people didn't.
That's critical for estimating the fraction of "roll-off" and "reverse roll-off" behavior.

The main problem that this code solves is to fill in the values of a 3x3 matrix that looks like:

|          | Trump      | Harris | No Vote   |
|----------|------------|--------|-----------|
| Robinson |            |        |           |
| Stein    |            |        |           |
| No Vote  |            |        |           |

In each precinct, we know the aggregate values (meaning we have the horizontal and vertical totals in our matrix).
But we don't know how those votes are distributed within the matrix ahead of time. 
It's entirely possible that lots of Stein voters voted for Trump and lots of Robinson voters voted for Harris, or that separate populations voted for President and Senate. 

The code in `ei.py` puts the raw data into a format that PyEI will handle, and then fits over the 2,861 precincts in North Carolina to fill in the missing values. 
In fact, the code also accounts for a fourth row and column (for "Other" candidates, including third-party and write-in candidates), but they are a tiny fraction of votes and are therefore generally negligible in discussion of the results.

Running this code takes quite a while (about 90 minutes). Here are the results after one run:

|               | Donald J. Trump | Kamala D. Harris | Other       | No Vote     |
|---------------|-----------------|------------------|-------------|-------------|
| Mark Robinson | 0.997843        | 0.00113712       | 0.000594623 | 0.000425297 |
| Josh Stein    | 0.135621        | 0.860806         | 0.00265666  | 0.000916604 |
| Other         | 0.740004        | 0.0191555        | 0.233781    | 0.00705974  |
| No Vote       | 0.0096037       | 0.00220907       | 0.00202395  | 0.986163    |

Your results may differ slightly, as the code relies heavily on MCMC sampling, so the outputs are liable to change.
Nevertheless, the results show that "roll-off" and "reverse roll-off" voting do not account for the difference in Trump and Robinson's performance - the answer is the prevalence of split-ticket voting.
About 13% of Stein voters voted for Trump, which was enough to give him the edge - no conspiracy theories needed.

## A note on data sources

Voter registration data was obtained from the [North Carolina State Board of Elections website](https://dl.ncsbe.gov/index.html?prefix=data/Snapshots).
Precinct-level results were similarly downloaded from the equivalent page [here](https://www.ncsbe.gov/results-data/election-results/historical-election-results-data#by-precinct).
All data was downloaded on or about 11/26/2024. 
