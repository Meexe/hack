from requests import get
from utils import vowels, punctuation
from re import findall


def check_rhyme(str1, str2, time1, time2):
    damage = 0

    str1 = str1.strip(punctuation)
    str2 = str2.strip(punctuation)
    str1 = str1.split(' ')
    str2 = str2.split(' ')

    if str1[-1][find_syllable(str1[-1])] == str2[-1][find_syllable(str2[-1])]:
        damage += 10

    if time2 > time1:
        damage += 10

    return damage


def find_syllable(word):

    resp = get(f'http://где-ударение.рф/в-слове-{word}/')

    for index in range(len(word)):
        letter = word[index]
        pattern = word[:index]+'<b>'+letter.upper()+'</b>'+word[index+1:]
        if (letter in vowels) & (findall(pattern, resp.text) != []):
            return index


if __name__ == '__main__':
    str1 = 'Я памятник себе воздвиг нерукотворный, '
    str2 = 'Вознесся выше он главою непокорной '
    result = check_rhyme(str1, str2, 0, 0)
    print(result)
