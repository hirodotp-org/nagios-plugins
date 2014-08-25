#! /usr/bin/env python

"""Check Bacula
 A nagios plugin using the pynagios module. It is used to check
 bacula for the completion of a single bacula job.
"""

# Copyright 2012 Oregon State University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


ERR=[]

try:
    from pynag.Plugins import PluginHelper, ok, warning, critical, unknown
except ImportError, err:
    ERR.append("%s" % err)

try:
    import MySQLdb as mysqldb
    from MySQLdb import cursors
except ImportError, err:
    ERR.append("%s" % err)

# Print 'Crit:' followed by all errors
if(ERR):
    print "%s %s" % ("CRIT:","; ".join(ERR))
    exit()

class BaculaCheck(PluginHelper):
	"""
	Nagios plugin to check if bacula is running on host.
	"""

	def setup(self):
		self.parser.add_option("-m", help="bacula database title (default: 'bacula')", dest='database', default='bacula')
		self.parser.add_option("-s", help="database hostname", dest='hostname', default='')
		self.parser.add_option('-t', help="limit check to within last HOURS", dest='hours', default='72')
		self.parser.add_option('-j', help="bacula job to check", dest="job")
		self.parser.add_option('-u', help="database user", dest="username")
		self.parser.add_option('-p', help="database password", dest="password")
		self.parser.add_option('-o', help="database port", dest="port")
		self.parse_arguments()

	def check(self):
		"""
		Nagios check main function
		"""
		self.options.host = self.options.hostname
		opts = self.options

		# Grab only hostname, username, password and port.
		conn_fields = dict((k, v) for (k, v) in vars(opts).items()
		if v is not None and k in ('host', 'user', 'passwd', 'port'))

        	# Create db connection
        	try:
            		self.conn = mysqldb.connect(db=opts.database,
                	cursorclass=mysqldb.cursors.DictCursor,
                	**conn_fields)
        	except mysqldb.Error, err:
            		return self.exit(summary="Could not connect to database", long_otput=err.args[1], exit_code=unknown, perfdata='' )

        	# Create a cursor, given the db connection succeeded
        	cursor = self.conn.cursor()

        	if hasattr(opts, 'job') and opts.job is not None:
            		# Check a single job
            		value = check_single_job(cursor, opts)
            		self.add_summary("Found %s successful Bacula jobs for %s" % (value, opts.job))
			self.add_metric(label='jobs', value=int(value))
        	else:
            		# Check all jobs
            		value = check_all_jobs(cursor, opts)
            		self.add_summary("%(status)s%% jobs completed | (%(success)s/%(total)s) jobs.  Failed jobs: %(errors)s" % value)
			self.add_metric(label='jobs_complete', value=int(value['status']))

        	# Clean up!
        	cursor.close()
        	self.conn.close()

		self.check_all_metrics()
		self.exit()

def check_single_job(cursor, opts):
    """
    Given a single job, get a count of it's status in the last given hours
    """
    cursor.execute(
        """
        SELECT COUNT(*) as 'count'
        FROM Job
        WHERE (Name='%(job)s') AND (JobStatus='T')
          AND (EndTime <= NOW() AND
             EndTime >= SUBDATE(NOW(), INTERVAL %(hours)s HOUR))
        """ % (vars(opts))
    )

    # Get and return job count
    status = cursor.fetchone()["count"]
    return status

def check_all_jobs(cursor, opts):
    """
    Check all the jobs from bacula and list the ones that have failed
    recently
    """
    cursor.execute(
        """
        select (
            select COUNT(JobId)
            from Job
            where JobStatus = 'T' and
                EndTime >= DATE_SUB(CURDATE(), INTERVAL %(hours)s HOUR)
            )
        as 'success', (
            select count(JobId)
            from Job
            where EndTime >= DATE_SUB(CURDATE(), INTERVAL %(hours)s HOUR)
        ) as 'total';
        """ % (vars(opts))
    )

    # Grab successful and total jobs
    row = cursor.fetchone()
    success = row["success"]
    total = row["total"]

    cursor.execute(
        """
        select Name
        from Job
        where JobStatus != 'T' and
            EndTime >= DATE_SUB(CURDATE(), INTERVAL %(hours)s HOUR)
        group by Name;
        """ % (vars(opts))
    )

    # Grab job Names
    jobs = cursor.fetchall()
    errored_jobs = [job["Name"] for job in jobs]

    try:
        status = int((success/float(total))*100)
    except ZeroDivisionError:
        status = 0

    return dict(
        status=status,
        success=success,
        total=total,
        errors=", ".join(errored_jobs))

if __name__ == "__main__":
    # Build and Run the Nagios Plugin
    plugin = BaculaCheck()
    plugin.setup()
    plugin.check()
