import streamlit as st
from typing import Callable
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
import time

def setup_tasks(funcs: list[Callable]):
    threads = [threading.Thread(target=func) for func in funcs]
    for thread in threads:
        add_script_run_ctx(thread)
        thread.start()

    for thread in threads:
        thread.join()


def counter():
    for x in range(3):
        st.write(x)
        time.sleep(1)

if st.button("Start counter"):
    setup_tasks([counter])
