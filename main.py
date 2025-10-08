def is_palindrome(text: str) -> bool:
    norm = "".join(ch.lower() for ch in text if ch.isalnum())
    return norm == norm[::-1]

def fibonacci(n: int) -> int:
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a

def count_vowels(text: str) -> int:
    vowels=set("aeiouy")
    norm = (text.lower())
    return sum (1for ch in norm if ch in vowels)

def calculate_discount(price: float, discount: float) -> float:
    if not (0.0 <=discount <=1.0):
        raise ValueError("musi byc miedzy [0,1]")
    return price * (1-discount)
def flatten_list(nested_list: list) -> list:
    o =[]
    for i in nested_list:
        if isinstance(i,list):
            o.extend(flatten_list(i))
        else:
            o.append(i)
    return o
def word_frequencies(text: str) -> dict:
    tokens: list[str] = text.lower().replace(',', '').replace('.', '').split()
    freqs = {}
    for token in tokens:
        if token in freqs:
            freqs[token] += 1
        else:
            freqs[token] = 1
    return freqs
def is_prime(n: int) -> bool:
    if n==2 or n==3: return True
    if n%2==0 or n<2: return False
    for i in range(3, int(n**0.5)+1, 2):   # only odd numbers
        if n%i==0:
            return False

    return True
