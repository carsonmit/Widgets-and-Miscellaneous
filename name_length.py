import math

def name_length(fname, lname):
    """
    This function takes the first and last name of the user and finds the length of the combined string
    """
    return(len(str(fname) + str(lname)))

firstname = input("Enter your first name:")
lastname = input("Enter your last name:") # Asks the user to input first and last names

print("The number of letters in your name is:" + str(name_length(firstname, lastname)))
    # Evaluates name_length given user input