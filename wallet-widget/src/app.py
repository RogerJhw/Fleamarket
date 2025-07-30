import streamlit as st
import streamlit.components.v1 as components

components.html(
    '<iframe src="http://localhost:5173" width="100%" height="600" frameBorder="0"></iframe>',
    height=600
)