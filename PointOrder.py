import fractions as f


def order(x, y, b):
    i = 1
    twop = double(x,y,b)
    x0 = twop[0]
    y0 = twop[1]
    while True:
        i += 1
        if i > 1000:
            print("Timeout error: order either > 1000 or infinite")
            break
        try:
            p = add(x0,y0,x,y)
            x0 = p[0]
            y0 = p[1]
        except ZeroDivisionError:
            print("Point has order" + i)
            break
    return


# adds points (x1,y1) and (x2,y2) under elliptic curve group law, curve y^2 = x^3 + bx + c
def add(x1: object, y1: object, x2: object, y2: object) -> object:
    l = (y2 - y1) / (x2 - x1)  # slope of line between points
    n = y1 - x1*l  # y-intercept of line between points
    x = l**2 - x1 - x2  # x-coordinate of third rational point intersecting line on curve
    y = l**3 - (x1 + x2)*l + n  # y-coordinate
    print(x, y)
    return x, y


def double(x, y, b):
    l = f.Fraction((3 * x**2 + b) / (2*y)).limit_denominator()  # slope of tangent line at point
    n = y - x*l  # y-intercept of line
    xx = l**2 - 2*x  # x-coordinate of second rational point intersecting line on curve
    yy = l**3 - 2*x*l + n  # y-coordinate
    print(xx, -yy)
    return xx, -yy


order(-2,3,0)


add(-2, 3, f.Fraction(19/25).limit_denominator(), f.Fraction(-522/125).limit_denominator())
