
let cityData
let forecast
let ctx
let overlayCtx
let selectedMetric = 2
let selectedDay = 0
let date_names = []

let selectedCityLat = 0
let selectedCityLon = 0

$( document ).ready(function() {
    clearError()

    // Do Loading Screen
    ticks = 0;
    setInterval(() => {
        $(".loading-text").html("Loading" + ".".repeat((ticks % 3) + 1))
        ticks++
    }, 500);

    // Calculate date names
    let date = new Date()
    for(let i = 0; i < 3; i++) {
        date_names.push(date.toDateString())
        date.setDate(date.getDate()+1);
    }

    // Load in cities for frontend
    loadCities()

    // Get forecast Button
    $("#get-forecast").click(() => {
        clearError()

        let locationInput = $("#forecast-location-input").val()
        let location = toLatLon(locationInput)
        if (location == null) {
            setError(`Could not parse location: ${locationInput}`)
            return
        }
        let [lat, lon] = location

        let [latIndex, lonIndex] = latLonToCoordinates(lat, lon)
        if (latIndex < 0 || latIndex >= PIXEL_HEIGHT || lonIndex < 0 || lonIndex >= PIXEL_WIDTH) {
            setError(`${lat}, ${lon} is out of range of prediction`)
            return
        }

        updateForecastCards(latIndex, lonIndex)
    })

    // Change forecast metric buttons
    $(".metric-button").each((i) => {
        $(".metric-button")[i].onclick = () => {
            selectedMetric = i
            drawForecast(ctx, selectedDay, selectedMetric)
        }
    })

    // Create Date change buttons
    let j = 0
    date_names.forEach(date_name => {
        $("#date-buttons").append(`<button type="button" class="btn btn-primary date-button">${date_name}</button>`)[0]
    });
    $(".date-button").each((i) => {
        $(".date-button")[i].onclick = () => {
            selectedDay = i
            drawForecast(ctx, selectedDay, selectedMetric)
        }
    })

    //Setup dynamic canvas
    $("#overlay-canvas")[0].onmousemove = (event) => {
        let x = event.offsetX / PIXEL_SIZE
        let y = event.offsetY / PIXEL_SIZE

        y = PIXEL_HEIGHT - y

        let xi = Math.floor(x)
        let yi = Math.floor(y)

        drawOverlay(forecast[selectedDay][yi][xi])
    }

    $("#overlay-canvas")[0].onmouseout = () => {
        drawOverlay()
    }

    // Get prediction from server
    axios.get("/getForecast").then((a) => {
        forecast = a.data.replace("NaN", "null")
        forecast = JSON.parse(a.data.replaceAll("NaN", "null"))

        onForecastRetrieved(forecast)
    })
});

const updateForecastCards = (latIndex, lonIndex) => {
    if(forecast[0][latIndex][lonIndex][0] == null) {
        setError("Could not find any data for this spot")
        return
    }

    $("#forecast").empty()

    selectedCityLat = latIndex
    selectedCityLon = lonIndex

    for(let day = 0; day < forecast.length; day++) {
        let values = forecast[day][latIndex][lonIndex]

        addCard(date_names[day], "", values)
    }

    drawOverlay()
}

const onForecastRetrieved = (forecast) => {
    // Setup canvas
    $("#forecast-map")[0].width = PIXEL_WIDTH * PIXEL_SIZE
    $("#forecast-map")[0].height = PIXEL_HEIGHT * PIXEL_SIZE
    ctx = $("#forecast-map")[0].getContext('2d')
    $("#overlay-canvas")[0].width = PIXEL_WIDTH * PIXEL_SIZE
    $("#overlay-canvas")[0].height = PIXEL_HEIGHT * PIXEL_SIZE
    overlayCtx = $("#overlay-canvas")[0].getContext('2d')

    drawForecast(ctx, 0, 2)

    // Get Milwaukke Forecast
    updateForecastCards(36, 74)
    
    // Remove loading screen
    $(".loading-subtext").html("Done")
    $(".loading-screen").fadeOut(700)
}

const drawOverlay = (mouseOverData) => {
    overlayCtx.clearRect(0, 0, PIXEL_WIDTH * PIXEL_SIZE, PIXEL_HEIGHT * PIXEL_SIZE);

    overlayCtx.strokeStyle = 'brown'
    overlayCtx.beginPath();
    overlayCtx.arc((selectedCityLon + 0.5) * PIXEL_SIZE, (PIXEL_HEIGHT - (selectedCityLat + 0.5) - 1) * PIXEL_SIZE, PIXEL_SIZE / 2, 0, 2 * Math.PI);
    overlayCtx.stroke();

    if(mouseOverData && mouseOverData[0] != null){
        console.log(mouseOverData)

        let labels = ["Max Temp", "Min Temp", "Avg Temp", "Humidity", "Pressure", "Wind X Dir", "Wind Y Dir", "Wind Spd"]
        const FONT_SIZE = 20
        ctx.font = `${FONT_SIZE}px serif`;


        for (let i = 0; i < 8; i++) {
            FONT_SIZE
            overlayCtx.fillText(labels[7 - i] + ": " + mouseOverData[7 - i], 2, (PIXEL_HEIGHT * PIXEL_SIZE) - ((i + 1) * (FONT_SIZE * 0.6)))
        }
    }
}

const PIXEL_SIZE = 8

const MINIMUM = [-92.1032913, -92.1032913, -92.1032913, 0.000692325368, 26.5815451, -1., -1.,  0.]
const MAXIMUM = [132.52376785, 132.52376785, 132.52376785, 100., 31.89179402, 1., 1., 108.47664471]

const drawForecast = (ctx, day, index) => {

    let grad = (index <= 2 ? temperatureGrad : grayscaleGrad)
    if (index == 7){
        grad = extremeGrad
    }

    for(let y = 0; y < PIXEL_HEIGHT; y++){
        for(let x = 0; x < PIXEL_WIDTH; x++) {
            let val = forecast[day][y][x][index]
            if(val == null){
                continue
            }
            let normalized = (val - MINIMUM[index]) / (MAXIMUM[index] - MINIMUM[index])

            ctx.fillStyle = getColor(grad, normalized);
            ctx.fillRect(x * PIXEL_SIZE, (PIXEL_HEIGHT - y - 1) * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
        }
    }
}

const WEST_LON = -125
const EAST_LON = -67
const NORTH_LAT = 49
const SOUTH_LAT = 25
const PIXELS_PER_DEGREE = 2

const PIXEL_WIDTH = 116
const PIXEL_HEIGHT = 48

const latLonToCoordinates = (lat, lon) => {
    let lat_normalized = (lat - SOUTH_LAT) / (NORTH_LAT - SOUTH_LAT)
    let lon_normalized = (lon - WEST_LON) / (EAST_LON - WEST_LON)
    let lat_index = parseInt(lat_normalized * (NORTH_LAT - SOUTH_LAT) * PIXELS_PER_DEGREE)
    let lon_index = parseInt(lon_normalized * (EAST_LON - WEST_LON) * PIXELS_PER_DEGREE)
    return [lat_index, lon_index]
}

const toLatLon = (input) => {
    try {
        // Lat and Lon
        let re = /^\s*\(?\s*(-?\d*\.?\d*)\s*,\s*(-?\d*\.?\d*)\s*\)?\s*$/
        let match = re.exec(input)
        return [parseFloat(match[1]), parseFloat(match[2])]
    } catch (error) {
        
        try {
            let re = /^\s*([\s\w]*)/
            let match = re.exec(input)
            let city = match[1]

            cities = cityData.filter(a => {return a["city"] == city})
            return [cities[0]["lat"], cities[0]["lng"]]

        } catch {}

    }

    return null
}

const sleep = (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
  }

const loadCities = () => {
    axios.get("/cities.json").then((a) => {
        cityData = a.data
        a.data.forEach(element => {
            $("#cities").append(`<option value="${element["city"]}, ${element["state_name"]}">`)
        });
    })
}

const setError = (message) => {
    $("#error-message").show()
    $("#error-message").html("Error: " + message)
}

const clearError = () => {
    $("#error-message").hide()
}

const updateProgress = (text) => {
    $("#loading-sub-bar").html(text)
}

const doneLoading = () => {
    $("#loading-screen").fadeOut(1000, () => {$("#loading-screen").remove()})
}

const addCard = (dow, date, data) => {
    $('#forecast').append(`<div class="card">
        <div class="card-body">
            <h5 class="card-title">${dow}</h5>
            <h6 class="card-subtitle mb-2 text-muted">${date}</h6>
            <table class="forecast-table"style="width: 100%;">
                <tbody>
                    <tr>
                        <td>High Temperature</td>
                        <td>${data[0].toFixed(1)} &deg;F</td>
                    </tr>
                    <tr>
                        <td>Low Temperature</td>
                        <td>${data[1].toFixed(1)} &deg;F</td>
                    </tr>
                    <tr>
                        <td>Average Temperature</td>
                        <td>${data[2].toFixed(1)} &deg;F</td>
                    </tr>
                    <tr>
                        <td>Humidity</td>
                        <td>${data[3].toFixed(1)} %</td>
                    </tr>
                    <tr>
                        <td>Pressure</td>
                        <td>${data[4].toFixed(1)} inHg</td>
                    </tr>
                    <tr>
                        <td>Wind Speed</td>
                        <td>${data[7].toFixed(1)} kts</td>
                    </tr>
                    <tr>
                        <td>Wind Direction</td>
                        <td>${getWindDirection(data[5], data[6])}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`)
}

const getWindDirection = (xVec, yVec) => {

    let angle = (Math.atan2(yVec, xVec) * 57.2958) + 180 // 0 is West, 90 is South, 180 is East, 270 is North
    let bearings = ["W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE", "E", "ENE", "NE", "NNE", "N", "NNW", "NW", "WNW"]

    let bearing_count = bearings.length
    let offset = 360.0 * (1 / bearing_count) / 2
    let index = Math.floor(((angle + offset) / 360.0) * bearing_count)

    return bearings[index]
}

///////////////////// COLOR THINGS ////////////////////

const getColor = (grad, percentage) => {

    let num_colors = grad.length
    let spacing = 1 / (num_colors - 1)

    let lowerIndex = Math.max(0, Math.floor(percentage / spacing))
    let higherIndex = Math.min(num_colors - 1, Math.ceil(percentage / spacing))

    let perc = (percentage - (spacing * lowerIndex)) / spacing

    let col1 = grad[lowerIndex]
    let col2 = grad[higherIndex]

    return colLerp(col1, col2, perc)
}

const colLerp = (col1, col2, percentage) => {
    let r1 = parseInt(col1.substring(1,3),16)
    let g1 = parseInt(col1.substring(3,5),16)
    let b1 = parseInt(col1.substring(5,7),16)

    let r2 = parseInt(col2.substring(1,3),16)
    let g2 = parseInt(col2.substring(3,5),16)
    let b2 = parseInt(col2.substring(5,7),16)

    return "#" + lerp(r1,r2,percentage).toString(16).padStart(2,"0")
               + lerp(g1,g2,percentage).toString(16).padStart(2,"0") 
               + lerp(b1,b2,percentage).toString(16).padStart(2,"0")
}

const lerp = (a, b, t) => {
    return parseInt((1 - t) * a + t * b);
  }

const temperatureGrad  = [
    '#000000',
    '#222222',
    '#800080',
    '#0000FF',
    '#00FFFF',
    '#00FF00',
    '#FFFF00',
    '#FF0000',
    '#FFFFFF'
]

const grayscaleGrad  = [
    '#000000',
    '#555555',
    '#FFFFFF'
]

const extremeGrad  = [
    '#000000',
    '#F0F0F0',
    '#F2F0F2',
    '#F4F0F4',
    '#F6F0F6',
    '#F8F0F8',
    '#FAF0FA',
    '#FFFFFF'
]
