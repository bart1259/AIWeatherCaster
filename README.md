# Introduction

Many different varieties of models are used today to predict the weather. No model is perfect, and often human intervention is required to determine which model would be best in the current situation. With the emergence of artificial intelligence and deep learning, a new tier of unsupervised models can be used for this task. This report describes an effort to predict daily weather across the continental United States. 

The approach used is similar to frame prediction. Every day's weather is encoded as an image and then a convolution neural network aims to predict the next day's weather from the previous day's information. Like a color picture has RGB channels, each daily image has a channel for each weather metric (temperature, humidity, etc.) it represents.

## Markovian Dependence

For this model to work, the data must have markovian dependence. Markovian dependence means that the future can be predicted from the "present" without any knowledge of the past.

# Input

## The dataset

The National Center for Environmental Information (NCEI) hosts the Local Climatology Dataset (LCD) which provides global hourly weather reports for hundreds of stations and daily "Summaries of the Day" (the latter part proved to not be true for every weather station). The weather reports contained information about the temperature, humidity, pressure, wind, visibility, sky conditions, and precipitation.

## Data Pre-processing

The dataset contained many errors such as stations not recording data for months, stations recording some metrics and not others, and stations giving non-believable data (On April 17th, 2010, at 6:45 AM at Big Spring Mcmahon-Wrinkle-Bpg Airport, a 143-degree dry bulb temperature was reported which beats the world record highest air temperature by 9 degrees). Due to the difficulty of figuring out if the data makes logical sense or not, all the data was left in.

Since the dataset contained global information, only weather stations that were within 1-degree latitude or longitude of the United State's border were considered processed.

## Aggregation

The hourly data from these weather stations were then aggregated into: 

- High daily dry bulb temperature
- Low daily dry bulb temperature
- Average daily dry bulb temperature
- Average daily relative humidity
- Average daily sea-level pressure
- Average Wind Direction
- Average Wind Speed

To average the wind, every hourly wind measurement was treated like a vector. These vectors were then added up and averaged over the day. The wind data is stored as a normalized direction (windXDirection and windYDirection) and magnitude values.

![image](https://user-images.githubusercontent.com/21147581/167026902-2f916d6a-6fc0-49da-8e68-a2d755b11b1b.png)

This daily weather data could then be interpolated between the stations to fill in the missing information where there were no weather stations. Many interpolation strategies could be used for this: nearest, linear, or cubic. Cubic interpolation tended to extrapolate the data too much. Linear interpolation would keep the data within a reasonable range but would cause the network to predict the data around the station instead of at the station, where the data was accurate. Finally, nearest interpolation would cause hard edges between weather stations. In the end, a nearest blurred strategy was selected as that ensured the data around the station was accurate and the edges between stations were softer which made the prediction more reasonable. 

![image](https://user-images.githubusercontent.com/21147581/167027832-a953367d-e100-448f-a0cb-4930470a6869.png)

In total, 11,688 images of daily weather data were generated (1990 to 2021) for training.

## Normalization

The eight channels of our image must be normalized for the network to unbiasedly predict our data. The temperature channels are normalized from 0 to 1 with 0 and 1 being mapped to the minimum temperature and the maximum temperature, respectively. The pressure, humidity, wind x-direction, wind y-direction, and wind speed channels were normalized separately from 0 to 1.

## Masking

Since predicting above the bodies of water would be difficult, becasue there are few weather stations in the oceans and great lakes, a mask was constructed to zero any point not above land.

# The Model

## Baseline Model

The baseline model chosen for this project predicts the weather by guessing there will be no change from today to tomorrow. This model is simple, fast, and relatively accurate as the weather does not, usually, change drastically from one day to another. Mathematically:

$\hat{y}_t=y_{t-1}$

Where $\hat{y}_t$ is the weather prediction for time $t$ and $y_t$ is the actual weather at time $t$.

![image](https://user-images.githubusercontent.com/21147581/167027929-1a5e559f-79a8-40f0-8055-6a890aba0d28.png)

The baseline model had a mean squared error loss of 0.2334

## Model Architecture

4 Different model architectures were tried: 
- Simple convolutional neural network (CNN)
- 3D CNN convolving over space and time
- Convolutional LSTM
- A CNN with channels representing metrics and time

Below is a summary of the accuracies and time to train each model with their respective better than baseline percentages.

![image](https://user-images.githubusercontent.com/21147581/167028032-94bdf138-0320-47e5-9f9d-01564feb7c74.png)

The last option, the CNN with channels that represented metrics and time, had the best results and trained the quickly. 3 days of metric data were stacked to form the input of the network.

A hyperband search was conducted to find the optimal kernel size and filter size. The following was found to be optimal:

![image](https://user-images.githubusercontent.com/21147581/167028078-d4fc3d3f-9645-4a5b-82f6-2e01018c05e9.png)

## Hyperparameters

The hyperparameters were also optimized with the hyper band search. The ideal hyperparameters were found to be:

- Learning Rate: 0.0001
- Batch Size: 16
- Epochs: Until validation accuracy stopped improving (about 60 epochs)

## Training Time

On an Nvidia Tesla T4, one epoch took around 19 minutes to complete so in total the model took around 19 hours to train.

# Analysis

The final model had a loss of 0.0086954 which is 62.9% better than the baseline.

Looking at the error each metric can be misleading as only about 69% of the region is predictable, above land. Assuming that the model can perfectly predict the oceans, the error above the land would be much higher. We can multiply each error by a factor of 1.45 to account for this.

The average error in each metric is:

|Metric|Error|Adjusted Error|
|------|-----|--------------|
|Max Temp| 4.7567 | 6.8972 |
|Min Temp| 4.2554 | 6.1704 |
|Avg Temp| 3.7178 | 5.3908 |
|Humidity| 6.6639 | 9.6626 |
|Pressure| 0.10267 | 0.14887 |
|Wind X Dir| 0.3459 | 0.5016 |
|Wind Y Dir| 0.3644 | 0.5285 |
|Wind Speed| 2.4790 | 3.5946 |

The loss by pixels looks like:

![image](https://user-images.githubusercontent.com/21147581/167028138-3fdad1d1-b44f-420e-8589-42dcee537e2e.png)

The error is maximized on the west coast. There are two reasons why this could be. 

The first is mountains. The western United States has a mountainous environment in which the weather can change rapidly. It is no surprise that it is difficult to predict the weather here. 

![image](https://user-images.githubusercontent.com/21147581/167028234-c9f44bce-5497-49b1-8403-c4379a048ace.png)

Another reason the west coast performs so poorly is the wind. The wind in the west coast comes from the west. There is no data west of the west coast, so the A.I. cannot use that information to make an accurate prediction.

All the bodies of water are outlined in a higher loss. This could be due to bodies of water affecting the weather in unpredictable ways. Alternatively, the A.I. must predict the bodies of water as zeros, which means the kernels in the CNNs might blur some of those zeros to leak out into the land portions.

# Conclusion

In conclusion, a model that is 62.9 percent better than the baseline model. Although the model is nowhere near as good as modern models, for the size and simplicity, it fairs pretty well.
