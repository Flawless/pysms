def send_command(serial_port, command_b, answer=msg_ok, timeout=timeout):
    #serial_port.flushInput()
    serial_port.read(serial_port.inWaiting())
    serial_port.write(command_b)
    return wait_for(serial_port, answer, timeout)
def wait_for(serial_port, template, timeout=timeout):
    if template==None:
        template=msg_ok
        return_answer=True
    else:
        template=template
        return_answer=False
    answer=(b'')
    timestamp=time.time()
    while time.time()-timestamp<timeout and not template in answer and not msg_error in answer:
        answer+=serial_port.read(serial_port.inWaiting())
        time.sleep(0.1)
    logging.debug('Recieved from: *** %s ***: %s'%(serial_port.port,answer))
    if return_answer:
        return answer
    else:
        return template in answer
def check_power_on(serial_port):
    return send_command(serial_port, b'AT\r')
