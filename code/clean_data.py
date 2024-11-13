import numpy as np
import os
import pandas as pd
import yaml
from data_utils import *

# set working directory to file location and load config

set_working_dir()

# clean and merge datasets

clean_data()
