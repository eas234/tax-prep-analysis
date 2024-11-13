import numpy as np
import os
import pandas as pd
import yaml

# set working directory to file location
set_working_dir()

sys.path.insert(1, '../utils')
from data_utils import *

# clean and merge datasets
clean_data()
