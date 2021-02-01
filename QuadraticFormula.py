import math

print("") #Empty line for formatting
print("Quadratic equations are equations of the form ax^2+bx+c=0") #Introduction / Prompt 1 - Quadratic Eqs
print("") #Empty line for formatting
print("Oftentimes, we want to find values of x that make this equation true assuming")
print("x is a variable and a, b, and c are constants")
print("") #Empty line for formatting
input("Press enter to continue:")
print("") #Empty line for formatting

print("A helpful fact is that polynomials of degree n have n solutions!") #Prompt 2 - Solutions of Quadratic Eqs
print("They may be distinct real solutions, repeated real solution, or even pairs of complex solutions")
print("Thus, these second degree polynomials (quadratics) will always have two solutions!")
print("") #Empty line for formatting
print("If that gives you a headache, don't worry! That's what this program is for!!")
print("") #Empty line for formatting
print("Make sure you've set your equation equal to 0 and have identified the appropriate values for a, b, and c")
print("") #Empty line for formatting
print("Also, please use decimals - this program thinks fractions are icky! We'll attain numerical solutions.")
print("Rounding is okay, just try to be as precise as possible")
print("") #Empty line for formatting
input("When you're ready to begin, press enter:")
print("") #Empty line for formatting

user_a = float(input("Alright! First, enter the value of a:")) #Prompts 3-5 - User Values of a, b, and c
print("") #Empty line for formatting
user_b = float(input("Now, enter the value of b:"))
print("") #Empty line for formatting
user_c = float(input("Finally, enter the value of c:"))

DISCRIMINANT = (user_b)*(user_b)-(4)*(user_a)*(user_c) #Important constant that determines nature of solutions

def QuadraticFormula(a, b, c):
    """
    This formula takes constant inputs a, b, c and evaluates the quadratic formula for the three possible cases
    A numerical, floating-point solution is generated as output
    """
    if DISCRIMINANT > 0:
        x1 = ((-(user_b)) + (math.sqrt(DISCRIMINANT))) / (2 * (user_a))
        x2 = ((-(user_b)) - (math.sqrt(DISCRIMINANT))) / (2 * (user_a))
        return("Your two distinct real solutions are: " + str(x1) + " and " + str(x2))
    elif DISCRIMINANT == 0:
        x1 = (-(user_b)) / (2 * (user_a))
        x2 = (-(user_b)) / (2 * (user_a))
        return ("Your two repeated real solutions are: " + str(x1) + " and " + str(x2))
    else:
        real = (-(user_b)) / (2 * (user_a))
        comp1 = (math.sqrt((4)*(user_a)*(user_c)-(user_b)*(user_b))) / (2 * (user_a))
        comp2 = ((-1) * math.sqrt((4)*(user_a)*(user_c)-(user_b)*(user_b))) / (2 * (user_a))
        x1 = complex(real, comp1)
        x2 = complex(real, comp2)
        return ("Your two complex conjugate solutions are: " + str(x1) + " and " + str(x2))

print(QuadraticFormula(user_a, user_b, user_c))