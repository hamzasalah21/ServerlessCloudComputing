from random import random
import threading
import time

result = None

def background_calculation():
    time.sleep(10) # waits for 10 seconds

    # when the calculation is done, the result is stored in a global variable
    global result
    result = "The weather is sunny in Montreal."

def main():
    counter = 0
    while True:
        thread = threading.Thread(target=background_calculation)
        thread.start()

        # TODO: wait here for the result to be available before continuing!

        thread.join()
        print('The result is', result)
        counter += 1
        if counter == 20:
            break

if __name__ == '__main__':
    main()