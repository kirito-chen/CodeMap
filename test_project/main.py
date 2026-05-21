from helper import greet
from utils import multiply

def start():
    print("Starting...")
    result = multiply(3, 4)
    greet("World")
    return result

if __name__ == "__main__":
    start()