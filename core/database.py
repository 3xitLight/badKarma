#!/usr/bin/env python3
# badKarma - advanced network reconnaissance toolkit
#
# Copyright (C) 2018 <Giuseppe `r3vn` Corti>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update

from libnmap.parser import NmapParser
from xml.etree import ElementTree

import json

Base = declarative_base()

class nmap_host(Base):
	__tablename__ = "nmap_host"

	id            = Column(Integer, primary_key=True)
	address       = Column(String(50))
	os_match      = Column(Text)
	os_accuracy   = Column(Text)
	ipv4          = Column(String(50))
	ipv6          = Column(String(250))
	mac           = Column(String(50))
	status        = Column(String(50))
	tcpsequence   = Column(String(200))
	hostname      = Column(Text)
	vendor        = Column(Text)
	uptime        = Column(String(100))
	lastboot      = Column(String(100))
	distance      = Column(Integer)
	latitude      = Column(Float)
	longitude     = Column(Float)
	scripts       = Column(Text)

class nmap_port(Base):
	__tablename__ = "nmap_port"

	id          = Column(Integer, primary_key=True)
	port        = Column(Integer)
	protocol    = Column(String(3))
	service     = Column(String(200))
	fingerprint = Column(Text)
	state       = Column(String(200))
	banner      = Column(Text)
	host        = relationship(nmap_host)
	host_id     = Column(Integer, ForeignKey('nmap_host.id'))

class activity_log(Base):
	__tablename__ = "activity_log"

	id         = Column(Integer, primary_key=True)
	pid        = Column(Integer)
	start_time = Column(String(200))
	end_time   = Column(String(200))
	title      = Column(String(200))
	output     = Column(Text)
	extension  = Column(Text)

class notes(Base):
	__tablename__ = "notes"

	id      = Column(Integer, primary_key=True)
	host    = relationship(nmap_host)
	host_id = Column(Integer, ForeignKey("nmap_host.id"))
	title   = Column(String(200))
	text    = Column(Text)

class DB:

	def __init__(self, db_loc="/tmp/badkarma.sqlite"):

		engine = create_engine("sqlite:///"+db_loc)
		Base.metadata.create_all(engine)
		Base.metadata.bind = engine
		DBSession = sessionmaker(bind=engine)

		self.db_loc = db_loc
		self.session = DBSession()

		# nmap well known services file location
		self.nmap_service_loc = "/usr/share/nmap/nmap-services"


	def _find_nmap_service(self, port, trasport):
		""" search inside nmap well known services file"""

		with open(self.nmap_service_loc,'r') as f:
			for line in f.readlines():
				if str(port)+"/"+trasport in line:

					return line.split()[0]



	def import_shodan(self, json_file):
		""" import smap.py json output """

		file = open(json_file,'r')
		sp_out = file.read()
		file.close()

		smap_out = json.loads(sp_out)

		for host in smap_out:
			# get the os match

			if smap_out[host]["os"]:
				match = smap_out[host]["os"]
			else:
				match = ""

			# get the first hostname
			try:
				hostname = smap_out[host]["hostnames"][0]
			except:
				hostname = ""

			# check if the host is already in the db
			if self.host_exist(host):
				# update
				add_host = self.session.query(nmap_host).filter( nmap_host.address == host ).one()
				
				# update values only if there's more informations

				if len(hostname) > 0:
					add_host.hostname = hostname
				if len(match) > 0:
					add_host.os_match = match
				if len(add_host.status) > 0:
					add_host.status = "up"
				
				add_host.latitude = smap_out[host]["latitude"]
				add_host.longitude = smap_out[host]["longitude"]


			else:
				# add the host to the db
				add_host = nmap_host(address=host,scripts="", latitude=smap_out[host]["latitude"],longitude= smap_out[host]["longitude"],hostname=hostname, os_match=match, os_accuracy='', ipv4='', ipv6='', mac='', status="up", tcpsequence="", vendor="", uptime="", lastboot="", distance="")
			
			# commit to db
			self.session.add(add_host)
			self.session.commit()

			i = 0


			for port in smap_out[host]["ports"]:

				service = self._find_nmap_service(port,smap_out[host]["data"][i]["transport"])

				if self.port_exist(add_host.id, port, smap_out[host]["data"][i]["transport"]):
					# update the existing port
					add_port = self.session.query(nmap_port).filter( nmap_port.host_id == add_host.id, nmap_port.port == port, nmap_port.protocol == smap_out[host]["data"][i]["transport"] ).one()

					if len(service) > 0:
						add_port.service = service



				else:
					# add the new port
					add_port = nmap_port(port=port, protocol=smap_out[host]["data"][i]["transport"], service=service, fingerprint="", state="open", banner="", host = add_host)

				# commit to db
				self.session.add(add_port)

				i += 1

		self.session.commit()




	def import_masscan(self, xml):
		""" import masscan xml output """

		dom = ElementTree.parse(xml)
		scan = dom.findall('host')
		out = {}
		add_host = ""

		for s in scan:
			addr = s.getchildren()[0].items()[0][1]
			port = s.getchildren()[1].getchildren()[0].items()[1][1]

			try:
				service = s.getchildren()[1].getchildren()[0].getchildren()[1].items()[0][1]
			except: 
				service = ""
			try:
				banner = s.getchildren()[1].getchildren()[0].getchildren()[1].items()[1][1]
			except: 
				banner = ""
			try:
				port_state =  s.getchildren()[1].getchildren()[0].getchildren()[0].items()[0][1]
			except:
				port_state = ""

			try:
				proto = s.getchildren()[1].getchildren()[0].items()[0][1]
			except: 
				proto= ""


			if addr in out:
				if service != "title" and service != "":

					if self.port_exist(add_host.id, port, proto):
						# update the existing port
						add_port = self.session.query(nmap_port).filter( nmap_port.host_id == add_host.id, nmap_port.port == port, nmap_port.protocol == proto ).one()

						if len(service) > 0:
							add_port.service = service
						#if len(service.servicefp) > 0:
						#	add_port.fingerprint = str(service.servicefp)

						if len(port_state) > 0:
							add_port.state = port_state
						if len(banner) > 0:
							add_port.banner = banner

					else:
						# add the new port
						add_port = nmap_port(port=port, protocol=proto, service=service, fingerprint="", state=port_state, banner=banner, host = out[addr])

						# commit to db
						self.session.add(add_port)

			else:
				if self.host_exist(addr):

					add_host = self.session.query(nmap_host).filter( nmap_host.address == addr ).one()

				else:
					# add the host to the db
					add_host = nmap_host(address=addr,scripts="", latitude=0, longitude=0, hostname="", os_match="", os_accuracy="", ipv4=addr, ipv6="", mac="", status="up", tcpsequence="", vendor="", uptime="", lastboot="", distance="")
					
					# commit to db
					self.session.add(add_host)

				out[addr] = add_host

			self.session.commit()
			


	def import_nmap(self, xml):
		""" import an nmap xml output """

		report = NmapParser.parse_fromfile(xml)

		for host in report.hosts:
			# get os accuracy
			try:
				accuracy = str(host.os_class_probabilities()[0])
			except:
				accuracy = ""

			# get the os match
			try:
				match = str(host.os_match_probabilities()[0])
			except:
				match = ""

			# get the first hostname
			try:
				hostname = host.hostnames[0]
			except:
				hostname = ""

			# check if the host is already in the db
			if self.host_exist(host.address):
				# update
				add_host = self.session.query(nmap_host).filter( nmap_host.address == host.address ).one()
				
				# update values only if there's more informations
				if len(str(host.scripts_results)) > 3:
					add_host.scripts = str(host.scripts_results)
				if len(hostname) > 0:
					add_host.hostname = hostname
				if len(match) > 0:
					add_host.os_match = match
				if len(accuracy) >0:
					add_host.os_accuracy = accuracy
				if len(host.ipv4) > 0:
					add_host.ipv4 = host.ipv4
				if len(host.ipv6) > 0:
					add_host.ipv6 = host.ipv6
				if len(host.mac) > 0:
					add_host.mac = host.mac
				if len(host.status) > 0:
					add_host.status = host.status
				if len(host.tcpsequence) > 0:
					add_host.tcpsequence = host.tcpsequence
				if len(host.vendor) > 0:
					add_host.vendor = host.vendor
				if len(str(host.uptime)) > 0:
					add_host.uptime = host.uptime
				if len(str(host.lastboot)) > 0:
					add_host.lastboot = host.lastboot
				if len(str(host.distance)) > 0:
					add_host.distance = host.distance

			else:
				# add the host to the db
				add_host = nmap_host(address=host.address,scripts=str(host.scripts_results), latitude=0, longitude=0, hostname=hostname, os_match=match, os_accuracy=accuracy, ipv4=host.ipv4, ipv6=host.ipv6, mac=host.mac, status=host.status, tcpsequence=host.tcpsequence, vendor=host.vendor, uptime=host.uptime, lastboot=host.lastboot, distance=host.distance)
			
			# commit to db
			self.session.add(add_host)
			self.session.commit()

			for port in host.get_ports():

				service = host.get_service(port[0],port[1])

				if self.port_exist(add_host.id, port[0], port[1]):
					# update the existing port
					add_port = self.session.query(nmap_port).filter( nmap_port.host_id == add_host.id, nmap_port.port == port[0], nmap_port.protocol == port[1] ).one()

					if len(service.service) > 0:
						add_port.service = service.service
					if len(service.servicefp) > 0:
						add_port.fingerprint = str(service.servicefp)
					#print(service.servicefp)

					if len(service.state) > 0:
						add_port.state = service.state
					if len(service.banner) > 0:
						add_port.banner = service.banner

				else:
					# add the new port
					add_port = nmap_port(port=port[0], protocol=port[1], service=service.service, fingerprint=service.servicefp, state=service.state, banner=service.banner, host = add_host)

				# commit to db
				self.session.add(add_port)

		self.session.commit()

	def add_note(self, host_id, title, text):
		""" add a note """
		add_note = notes(host_id=host_id, title=title, text=text)

		self.session.add(add_note)
		self.session.commit()

		return title, self.session.query(notes).order_by(notes.id.desc()).first().id

	def add_host(self, address):
		""" add a host without scan it """
		add_host = nmap_host(address=address, latitude=0, longitude=0, os_match="", status="", hostname="", ipv4="", mac="", vendor="", tcpsequence="", scripts="{}")

		self.session.add(add_host)
		self.session.commit()

	def add_log(self, pid, start_dat, end_dat, title, output, extension):
		""" add activity log entry to the database """

		log_add = activity_log( pid=pid, start_time=start_dat, end_time = end_dat, title=title, output=output, extension = extension )
		self.session.add(log_add)
		self.session.commit()

		return self.get_log_id()

	def save_note(self, note_id, value):

		note = self.session.query(notes).filter( notes.id == note_id ).one()
		note.text=value
		self.session.commit()

	def host_exist(self, ipv4):
		# function to check if a host is already in the databse
		if len(self.session.query(nmap_host).filter( nmap_host.address == ipv4 ).all()) > 0:
			return True
		
		return False

	def port_exist(self, host_id, port, protocol):
		# function to check if a port is already in the database
		if len(self.session.query(nmap_port).filter( nmap_port.host_id == host_id, nmap_port.port == port, nmap_port.protocol == protocol ).all()) > 0:
			return True
		
		return False

	def get_note(self, note_id):
		return self.session.query(notes).filter( notes.id == note_id ).one()

	def get_notes(self, host_id):
		return self.session.query(notes).filter( notes.host_id == host_id ).all()

	def get_hosts(self):
		return self.session.query(nmap_host).all()

	def get_host(self, id):
		return self.session.query(nmap_host).filter( nmap_host.id == id ).one()

	def get_port(self,id):
		return self.session.query(nmap_port).filter( nmap_port.id == id ).one()

	def get_service(self, id):
		return self.session.query(nmap_port).filter( nmap_port.service == id ).all()

	def get_services_uniq(self):
		return self.session.query(nmap_port.service).distinct()

	def get_ports_by_service(self, service):
		return self.session.query(nmap_port).filter( nmap_port.service == service ).all()

	def get_ports_by_host(self, host):
		return self.session.query(nmap_port).filter( nmap_port.host == host ).all()


	def get_logs(self, id=''):
		if id == '':
			return self.session.query(activity_log).all()
		
		return self.session.query(activity_log).filter( activity_log.id == int(id) ).one()

	def get_history(self, host):
		return self.session.query(activity_log).filter( activity_log.title.like("%"+host+"%")).all()

	def get_log_id(self):
		return self.session.query(activity_log).order_by(activity_log.id.desc()).first().id

	def remove_log(self,id):
		todel = self.session.query(activity_log).filter( activity_log.id == id ).one()
		self.session.delete(todel)
		self.session.commit()

		return True

	def remove_note(self, id):
		todel = self.session.query(notes).filter( notes.id == id ).one()

		self.session.delete(todel)
		self.session.commit()

		return True


	def remove_host(self, id):
		#print(address)
		todel = self.session.query(nmap_host).filter( nmap_host.id == id ).one()
		todel_2 = self.session.query(nmap_port).filter( nmap_port.host_id == id ).all()

		self.session.delete(todel)
		for to in todel_2:
			self.session.delete(to)

		self.session.commit()


		return True
