This repo is a designated tracker and predictor for the Leeds United football club.
It uses the free version of TheSportsDB API, pandas and flask as the main imported libaires.
The prediction is primarily based off of the historic meetings between clubs, and is swayed / nudged based on Leeds United recent form.

This repo was made over summer between year 2 and year 3 of my Computer Science course.
And then extended on over year 3 of University as a personal project.
Hosted on https://predictor.hardcase.uk - Private home server


Weather API - uses coordinates and a date in order to find the relevent metrics.
the weather API returns hourly data for the whole day, and this is then used in order to make 
boolean variable types, isSunny, isCloudy and isWindy alongside a weather code based on how windy it is.
These variable types will all be compared from previous games in order to see if the weather
can affect the outcome of a match.