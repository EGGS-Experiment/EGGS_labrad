
    @setting(211, 'Current Set', curr_ma='v', returns='v')
    def currentSet(self, c, curr_ma=None):
        """
        Get/set the set output current.
        Arguments:
            curr_ma (float) : the output current (in mA).
        Returns:
                    (float) : the output current (in mA).
        """
        # setter
        if curr_ma is not None:
            if (curr_ma < 0) or (curr_ma > 80):
                raise Exception("Error: set current must be in range (10, 35) mA.")
            yield self.ser.acquire()
            yield self.ser.write('iout.na.w {:f}\r\n'.format(curr_ma * 1e6))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('iout.na.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip()) / 1e6
        self.notifyOtherListeners(c, ('SET', resp), self.current_update)
        returnValue(resp)

    @setting(222, 'Current Max', curr_ma='v', returns='v')
    def currentMax(self, c, curr_ma=None):
        """
        Get/set the maximum output current.
        Arguments:
            curr_ma (float) : the maximum output current (in mA).
        Returns:
                    (float) : the maximum output current (in mA).
        """
        # setter
        if curr_ma is not None:
            if (curr_ma < 0) or (curr_ma > 80):
                raise Exception("Error: max current must be in range (10, 35) mA.")
            yield self.ser.acquire()
            yield self.ser.write('ilim.ma.w {:f}\r\n'.format(curr_ma))
            yield self.ser.read_line('\n')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('ilim.ma.r\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse resp
        resp = float(resp.strip())
        self.notifyOtherListeners(c, ('SET', resp), self.current_update)
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(AMO1Server())
