#Scrabble Score Dictionary
score_dict = {
    "A" : 1,
    "a" : 1,
    "B" : 3,
    "b" : 3,
    "C" : 3,
    "c" : 3,
    "D" : 2,
    "d" : 2,
    "E" : 1,
    "e" : 1,
    "F" : 4,
    "f" : 4,
    "G" : 2,
    "g" : 2,
    "H" : 4,
    "h" : 4,
    "I" : 1,
    "i" : 1,
    "J" : 8,
    "j" : 8,
    "K" : 5,
    "k" : 5,
    "L" : 1,
    "l" : 1,
    "M" : 3,
    "m" : 3,
    "N" : 1,
    "n" : 1,
    "O" : 1,
    "o" : 1,
    "P" : 3,
    "p" : 3,
    "Q" : 10,
    "q" : 10,
    "R" : 1,
    "r" : 1,
    "S" : 1,
    "s" : 1,
    "T" : 1,
    "t" : 1,
    "U" : 1,
    "u" : 1,
    "V" : 4,
    "v" : 4,
    "W" : 4,
    "w" : 4,
    "X" : 8,
    "x" : 8,
    "Y" : 4,
    "y" : 4,
    "Z" : 10,
    "z" : 10,
    " " : 0
}

x = str(input("Enter a word/phrase to find its Scrabble Score!:"))
score = 0
for i in x:
    score += score_dict[i]
print("The Scrabble Score of " + x + " is " + str(score))
if score >= 0 and score < 10:
    print("That's not a ton of points, but it's a start - nice work!")
elif score >= 10 and score < 20:
    print("That's a pretty good score! Can you get a higher score with a one-word answer?")
    print("Hint: it has to be in the Scrabble Dictionary")
elif score >= 20 and score < 30:
    print("Holy cow! That's a big score! If that was just one word, I'm impressed!")
elif score >= 30 and score < 40:
    print("You're a Scrabble wizard! The most valuable word in the Scrabble dictionary")
    print("is worth 41 points. Can you guess what it is?")
elif score >= 40:
    print("Not many can do what you just did! Did you know the most valuable word in the")
    print("Scrabble Dictionary is Oxyphenbutazone worth a whopping 41 points!!")
    print("Were you able to guess this word?")
else:
    print("Error")