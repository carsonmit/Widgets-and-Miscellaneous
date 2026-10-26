import itertools

n = 3
array = [i for i in range(n+1)]
print(array)
for x in itertools.combinations_with_replacement(array, n):
    if 0 <= x[0] and x[0] <= (x[1]/2) and (x[1]/2) <= (x[2]/3) and (x[2]/3) <= 1: # (x[3]/4) and (x[3]/4) <= 1:
        print(x)
