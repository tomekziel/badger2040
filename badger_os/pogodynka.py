# Pogodynka for Badger 2040W
# MIT License
# Tomasz Zielinski (tomasz.zielinski@gmail.com)

# Inspired heavily by Badger 2040 MicroPython Examples
# https://github.com/pimoroni/badger2040/blob/main/badger_os/examples/weather.py

import badger2040
import urequests
import pngdec
import math

print("POGODYNKA IS STARTING")

DEGREES = 5  # temperature scale segments in Celsius degrees
HOURS = 24   # forecast in hours
WIDTH = 296  # screen width

# Wroclaw latitude/longitude, Europe/Berlin timezone
URL = "https://api.open-meteo.com/v1/forecast?latitude=51.107883&longitude=17.038538&current_weather=true&current=temperature_2m&hourly=temperature_2m,precipitation,weather_code,is_day&timezone=Europe%2FBerlin&forecast_days=3"

# reconnection attempts
attempts = 0

# callback of wifi connection
def custom_status_handler(mode, status, ip):
    global attempts
    print(mode, status, ip)
    if status:  #connected
        display.display.set_pen(15)
        display.display.clear()
        display.display.set_pen(0)        
        attempts = 0
    elif status is None: #not connected
        attempts += 1
    else: #not connected
        attempts += 1

    #up to 20 dots on counter
    attempts = min(attempts,20)
    print(f"attempt {attempts}")

    if (attempts>0):
        display.set_update_speed(badger2040.UPDATE_FAST)
        png.open_file("/cyfry/dot.png")
        for i in range(0, attempts):
            png.decode(WIDTH-(8*(i+1)), 120)
        display.partial_update( WIDTH-(8*attempts) ,120,8*attempts,8)
        display.set_update_speed(badger2040.UPDATE_NORMAL)

# downloading data from Open-Meteo
def get_data():
    global weathercode, temperature, date, time, hour, temparr, tempmin, tempmax, hoursarr, dayarr, preciarr
    print(f"Requesting URL: {URL}")
    r = urequests.get(URL)
    # open the json data
    j = r.json()
    print("Data fetched")
    #print(j)

    # parse relevant data from JSON
    current = j["current_weather"]
    temperature = current["temperature"]
    
    date, time = current["time"].split("T")
    hour = time.split(":")[0]
    
    subarray = j["hourly"]["temperature_2m"]
    X = int(hour)
    temparr = subarray[X:X + HOURS]
    #temparr = [s*2+27 for s in temparr]  # testing wider temperature range 
    #print(temparr)

    hoursarr = j["hourly"]["time"]
    hoursarr = hoursarr[X:X + HOURS]
    hoursarr = [timestamp.split("T")[1].split(":")[0] for timestamp in hoursarr]
    hoursarr = [int(s) for s in hoursarr]
    #print(hoursarr)

    dayarr = j["hourly"]["is_day"]
    dayarr = dayarr[X:X + HOURS]
    dayarr = [int(s) for s in dayarr]
    #print(dayarr)

    preciarr = j["hourly"]["precipitation"]
    preciarr = preciarr[X:X + HOURS]
    preciarr = [int(s) for s in preciarr]
    preciarr = [ min(10, s) for s in preciarr]  # up to 10 mm of rain per hour
    #preciarr = [ max(0, math.sin(s)*6) for s in hoursarr]  # testing precipitation
    #preciarr[6] = 9.5
    #preciarr[7] = 10
    #print(preciarr)

    weathercodearray = j["hourly"]["weather_code"]
    weathercodearray = weathercodearray[X:X + 6]
    weathercodearray = [int(s) for s in weathercodearray]
    weathercode = max(weathercodearray)

    tempmin = math.floor(min(temparr) / DEGREES) * DEGREES
    tempmax = math.ceil(max(temparr) / DEGREES) * DEGREES
    
    #print(tempmin, tempmax)
    
    r.close()

# nighttime ranges
def find_nights(array):
    clusters = []
    start = None
    
    for i, value in enumerate(array):
        if value == 0 and start is None:  # Start of a cluster
            start = i
        elif value == 1 and start is not None:  # End of a cluster
            clusters.append((start, i - 1))
            start = None

    # If the array ends with a cluster of 1s
    if start is not None:
        clusters.append((start, len(array) - 1))
    
    return clusters

# print small digit on scale
def print_small(number, x, y):
    swidths = [6, 4, 6, 6, 7, 6]
    digit = abs(number)%10
    png.open_file(f"/cyfry/s{digit}.png")
    png.decode(x - swidths[digit], y-4)
    x -= swidths[digit]+1
    if ( abs(number)>=10 ):
        digit = math.floor(abs(number)/10)
        png.open_file(f"/cyfry/s{digit}.png")
        png.decode(x - swidths[digit], y-4)
        x -= swidths[digit]+1
    
    if ( number < 0):
        png.open_file(f"/cyfry/sminus.png")
        png.decode(x - 5, y-4)
    
    display.set_pen(0)

# draw the whole page
def draw_page():
    global X, Y, W, H
    
    # Clear the display
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
  

    if temperature is not None:

        LEGEND = 20
        
        display.set_pen(0)
        
        digitswidth = [38,26,34,36,39,36,37,33,39,37]
        minuswidth = 20  #18+4
        celsiuswidth = 18

        t = round(temperature)
        #t = -20
        twidth = 0
        if (t<0):
            #print(f"minus")
            twidth += minuswidth
            LEGEND += 4
            
        if (t <= -10 or t >= 10):
            #print(f"decimals {abs(t)%10}")
            twidth += digitswidth[ math.floor(abs(t)/10) ]
            LEGEND += 8
            
        #print(f"ones {abs(t)%10}")
        twidth += digitswidth[ abs(t)%10 ]

        twidth += celsiuswidth
       
        #print(f"width {twidth}")

        tmargin = (64-min(twidth,64))/2
        tmargin = round(tmargin)
        #print(f"tmargin {tmargin}")
        
        if (t<0):
            png.open_file("/cyfry/minus.png")
            png.decode(tmargin, 3)
            tmargin += minuswidth

        if (t <= -10 or t >= 10):
            png.open_file(f"/cyfry/{math.floor(abs(t)/10)}.png")
            png.decode(tmargin, 0)
            tmargin += digitswidth[ math.floor(abs(t)/10) ] + 4

        
        png.open_file(f"/cyfry/{abs(t)%10}.png")
        png.decode(tmargin, 0)
        tmargin += digitswidth[ abs(t)%10 ] + 4

        png.open_file("/cyfry/celsius.png")
        png.decode(tmargin, 5)

        tmargin += celsiuswidth
        
        tmargin = max(64, tmargin)
        tmargin += LEGEND
        #print(f"LEGEND {LEGEND}")

        display.set_pen(0)


        X = tmargin
        Y = 5        
        W = WIDTH-X-1
        H = 100

        #print(f"X {X}")


        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        # Weather icons from https://fontawesome.com/
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            png.open_file("/icons/icon-snow.png")
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            png.open_file("/icons/icon-rain.png")
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            png.open_file("/icons/icon-cloud.png")
        elif weathercode in [0]:  # codes for sun
            png.open_file("/icons/icon-sun.png")
        elif weathercode in [95, 96, 99]:  # codes for storm
            png.open_file("/icons/icon-storm.png")
        png.decode(round((X-LEGEND-64)/2), 63)        
        
        
        # night
        display.set_pen(8)
        nights = find_nights(dayarr)
        for i, (start, end) in enumerate(nights):
            #print(f"Cluster {i + 1}: Start = {start}, End = {end}")
            display.rectangle(X+int(start*W / (HOURS-1)), Y+1, int( (end-start)*W / (HOURS-1) ), H-2)


        display.set_pen(0)        
        display.line(X, Y, X, Y+H, 2)
        
        # lines horiz
        multi = 2
        for y in range(tempmin, tempmax+DEGREES):
            display.set_pen(0)
            display.line(X-3, getY(y), X, getY(y), 1)
            if (y == 0):
                display.line(X-6, getY(y), X, getY(y), 1)
                print_small(y, X-7, getY(y))
                display.line(X, getY(y), X+W, getY(y),2)
            elif(y%DEGREES == 0):
                display.line(X-6, getY(y), X, getY(y), 1)
                print_small(y, X-7, getY(y))
                lightLineHor(X, X+W, getY(y))
            else:
                lightLineHor(X, X+W, getY(y),5)
        


        STEP = W / (HOURS-1)
        sx = X
        
        # PRECIP BOXES
        i = 0
        for p in preciarr:
            if (p>0):
                pheight = round(p/10*H/2)
                display.display.set_pen(0) #black box
                pw = math.ceil((i+1)*STEP)-math.ceil(i*W / (HOURS-1))
                display.rectangle(X+math.ceil(i*STEP)-1, Y+H-pheight, pw+1, pheight)
                display.display.set_pen(15) #white box
                display.rectangle(X+math.ceil(i*STEP), Y+H-pheight+1, pw-1, pheight-2)
            i += 1        
        
        display.display.set_pen(0) #black box
        
        prevX = X
        prevY = round(getY(temparr[0]))
        
        # TEMPERATURE LINE
        i = 0
        for t in temparr:
            display.line(prevX, prevY, round(sx), getY(t),3)

            display.line(round(sx), Y+H, round(sx), Y+H+2)
            if ( hoursarr[i]%4 == 0):
                width = display.measure_text(str(hoursarr[i]), 0.5)
                display.text(str(hoursarr[i]), math.ceil(sx-width/2), Y+H+9, 200, 0.5 )
                display.line(round(sx), Y+H, round(sx), Y+H+6)
            prevX = round(sx)
            prevY = getY(t)                
            sx += STEP
            i += 1


    else:
        display.set_pen(0)
        display.rectangle(0, 60, WIDTH, 25)
        display.set_pen(15)
        display.text("Unable to display weather! Check your network settings in WIFI_CONFIG.py", 5, 65, WIDTH, 1)

    display.set_update_speed(badger2040.UPDATE_NORMAL)
    display.update()

# draw light hotizontal line
def lightLineHor(x1, x2, y, step=2):
    for x in range(x1, x2):
        if (x % step == 0):
            display.pixel(x, y)
    
# calculate Y for given temperature
def getY(temp):
    global X, Y, W, H, tempmin, tempmax
    scaled_value = Y+H - ((temp - tempmin) / (tempmax - tempmin)) * H
    return math.floor(scaled_value)

# Display Setup
display = badger2040.Badger2040()
display.led(128)
png = pngdec.PNG(display.display)


while True:

    try:
        # Connects to the wireless network. Ensure you have entered your details in WIFI_CONFIG.py :).
        display.connect(status_handler=custom_status_handler)
        get_data()
    except Exception as e:
        print(e)
        print(f"Caught exception: {e}")
        print("Restarting application...")
        continue    


    draw_page()
    display.led(0)

    print("Going to sleep")
    # Call halt in a loop, on battery this switches off power.
    # On USB, the app will exit when A+C is pressed because the launcher picks that up.
    display.keepalive()
    badger2040.sleep_for(1)
    badger2040.turn_off()


