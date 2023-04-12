# pouziti threadu - narozdil od asyncio - nemame pod tim uplnou kontrolu a ridi to knihovna
# thready jsou výhodne pro naročné IO operace, např. loadery, requestory, scrapery, ukladače atp.
# how to share data between Threads
# 1.Sharing a boolean variable with a threading.Event.
    # declare in unset or false state
    # event = threading.Event()
    # if event.is_set():     # check if set
    # event.set()     # set the event true 
    # event.clear()   #  or false

# 2.Protecting global shared data with a threading.Lock.
    # lock = threading.Lock()
    # with lock:
    #     variable = variable + 10

# 3.Sharing data with a queue.Queue. Queue can be shared between threads.
    # create a queue
    # queue = Queue() #create FIFO
    # queue.put(i)   #enque
    # data = queue.get() #dequeue

# dale je tu condition - takova roura mezi consumerem a producerem
    # cond = threading.Condition()
    # cond.wait()     #consumer waiting
    # cond.notifyAll() #producer notifiying consumer, they can continue
    # consumer threads wait for the Condition to be set before continuing.
    # The producer thread is responsible for setting the condition and notifying the other threads
    # that they can continue. Více v sam.test filu.


import threading

def do_first():
    print("Running do_first line 1")
    print("Running do_first line 2")
    print("Running do_first line 3")

def do_second():
    print("Running do_second line 1")
    print("Running do_second line 2")
    print("Running do_second line 3")

def main():
    t1 = threading.Thread(target=do_first)
    t2 = threading.Thread(target=do_second)

    # Start threads
    t1.start(), t2.start()

    # Wait threads to complete
    t1.join(), t2.join()

if __name__ == "__main__":
    main()