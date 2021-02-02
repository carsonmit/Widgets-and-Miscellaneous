def FtoC(F): #Function converting Fahrenheit to Celcius
    C = (5 / 9) * (F - 32)
    return C

def FtoK(F): #Function converting Fahrenheit to Kelvin
    K = ((5 / 9) * (F - 32)) + 273.15
    return K

def CtoF(C): #Function converting Celcius to Fahrenheit
    F = ((9 / 5) * C) + 32
    return F

def CtoK(C): #Function converting Celcius to Kelvin
    K = C + 273.15
    return K

def KtoC(K): #Function converting Kelvin to Celcius
    C = K - 273.15
    return C

def KtoF(K): #Function converting Kelvin to Fahrenheit
    F = ((9 / 5) * (K - 273.15)) + 32
    return F

# The main prompt and the interface the user interacts with
print("") #Empty line for formatting
print("Hi! Welcome to TemperatureConverter")
print("") #Empty line for formatting
print("1. Fahrenheit to Celcius")
print("2. Fahrenheit to Kelvin")
print("3. Celcius to Fahrenheit")
print("4. Celcius to Kelvin")
print("5. Kelvin to Celcius")
print("6. Kelvin to Fahrenheit")
print("") #Empty line for formatting
user_num = int(input("Please enter the number corresponding to your desired option:"))

# Conditional to determine which converter to activate given the input in user_num
if user_num == 1:
    print("")  # Empty line for formatting
    print("Fahrenheit to Celcius it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Fahrenheit:"))
    print("")  # Empty line for formatting
    output = FtoC(user_temp)
    print(str(user_temp) + " degrees Fahrenheit is equivalent to " + str(output) + " degrees Celcius")
elif user_num == 2:
    print("")  # Empty line for formatting
    print("Fahrenheit to Kelvin it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Fahrenheit:"))
    print("")  # Empty line for formatting
    output = FtoK(user_temp)
    print(str(user_temp) + " degrees Fahrenheit is equivalent to " + str(output) + " Kelvin")
elif user_num == 3:
    print("")  # Empty line for formatting
    print("Celcius to Fahrenheit it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Celcius:"))
    print("")  # Empty line for formatting
    output = CtoF(user_temp)
    print(str(user_temp) + " degrees Celcius is equivalent to " + str(output) + " degrees Fahrenheit")
elif user_num == 4:
    print("")  # Empty line for formatting
    print("Celcius to Kelvin it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Celcius:"))
    print("")  # Empty line for formatting
    output = CtoK(user_temp)
    print(str(user_temp) + " degrees Celcius is equivalent to " + str(output) + " Kelvin")
elif user_num == 5:
    print("")  # Empty line for formatting
    print("Kelvin to Celcius it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Kelvin:"))
    print("")  # Empty line for formatting
    output = KtoC(user_temp)
    print(str(user_temp) + " Kelvin is equivalent to " + str(output) + " degrees Celcius")
elif user_num == 6:
    print("")  # Empty line for formatting
    print("Kelvin to Fahrenheit it is!")
    print("")  # Empty line for formatting
    user_temp = float(input("Enter a temperature in Kelvin:"))
    print("")  # Empty line for formatting
    output = KtoF(user_temp)
    print(str(user_temp) + " Kelvin is equivalent to " + str(output) + " degrees Fahrenheit")
else:
    print("") # Empty line for formatting
    print("Uh oh! I don't think that was one of the options - please try again")