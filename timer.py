from threading import Event, Thread

def echo(str):
    print str

def call_repeatedly(interval, func, *args):
    stopped = Event()
    def loop():
        while not stopped.wait(interval): # the first call is in `interval` secs
            func(*args)
    Thread(target=loop).start()    
    return stopped.set

cancel_future_calls = call_repeatedly(3, echo, "Hello, World")
# ...
#cancel_future_calls() 
