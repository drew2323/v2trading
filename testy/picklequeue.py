import queue
import msgpack
# Creating the original queue
original_queue = queue.Queue()
new_queue = queue.Queue()

# Adding elements to the original queue
original_queue.put(5)
original_queue.put(10)
original_queue.put(15)

# Pickling the queue
pickled_queue = msgpack.packb(original_queue)

# Unpickling the queue
unpickled_queue = msgpack.unpackb(pickled_queue)
# Pickling the queue
new_queue.queue = unpickled_queue.queue


print(new_queue)

# Checking the contents of the new queue
while not new_queue.empty():
    print(new_queue.get())