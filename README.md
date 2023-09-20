# EcoDrive

## Introduction

This program utilises the power of quantum annealing to formulate an efficient path for drivers to take while not carrying riders, to optimise the driver's fuel usage, time, and rider pickups.

## Installation

Clone the Github Repository and install the necessary packages.\
The two necessary packages are Flask and the Dwave Ocean SDK.\
\
To install Flask:\
```pip install Flask```

To install the Dwave Ocean SDK:\
```pip install dwave-ocean-sdk```

## Running the Server

Once everything is installed, in the root of the repository, run:\
```flask --app main.py run```\

Now requests can be made to the code.

## Usage

Once the server is running, requests can be made localhost.
The route that the requests must be made to is ```/route```

The data has to be sent along with a request body, made up of JSON with two properties: ```num_nodes``` and ```edges```.\
```num_nodes``` is simply the number of nodes (or points to reach) that will be in the final graph.\
```edges``` is a list of road data provided in the form:\
"point1 point2 property1 property2 property3"\
The points are the two edges of the segment of road being entered. The properties are the aspects of that leg of the journey that should be taken into consideration. Here they would be, time spent on that road, due to distance and traffic, number of other uber drivers on or close to that road, and the demand on that road.

All this data can be easily provided by Uber.