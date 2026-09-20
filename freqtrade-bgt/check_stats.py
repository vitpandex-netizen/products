import sqlite3
import glob

dbs = glob.glob('/Users/vitaliyr/dev/freqtrade-bgt/user_data/tradesv3.dryrun*.sqlite')
# Note: since the db is mapped via volume, it should be in user_data of the mac? Wait! 
# We deployed to US server, but the user_data is mapped to the Mac? NO, the containers run on US server.
# Let's run the check on the US Server!
