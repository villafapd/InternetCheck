from threading import Timer


class Temporizador_offDelay():

    def __init__(self, t, hFunction):
        self.t = t
        self.hFunction = hFunction
        self.thread = Timer(self.t, self.handle_function)
        self.seguir_ejecutando = True
        
    def handle_function(self):
        self.hFunction()
        if self.seguir_ejecutando:
            self.thread = Timer(self.t, self.handle_function)
            self.thread.start()
        #self.thread = Timer(self.t, self.handle_function)
        #self.thread.start()
        
    def start(self):
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()
        
    def cancel(self):
        self.seguir_ejecutando = False
        self.thread.cancel()



