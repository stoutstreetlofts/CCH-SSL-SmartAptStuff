/**
 *  Copyright 2015 SmartThings
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at:
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
 *  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License
 *  for the specific language governing permissions and limitations under the License.
 *
 */
import groovy.json.JsonSlurper
import java.awt.Color

def rChild = bool
def gChild = bool
def bChild = bool
def w1Child = bool
def bulbCOLOR = bool
def bulbHUE = bool
def bulbSATURATION = bool
def bulbMODE = bool

metadata {

    definition (name: "Alexa-SmartLife Color Bulb", namespace: "starfleet", author: "stoutstreetlofts-smartthings") {
        capability "Switch"
        capability "Switch Level"
        
        
		capability "Actuator"	//included to give compatibility with ActionTiles
        capability "Sensor"		//included to give compatibility with ActionTiles
        
        capability "Bulb"
        capability "Light"
        capability "Color Control"
        capability "ColorTemperature"
        
		capability "Refresh"
        capability "Configuration"
        capability "Health Check"
		
        attribute "about", "string"
    
        (1..6).each { n ->
        	attribute "light$n", "enum", ["on", "off"]
            command "on$n"
            command "off$n"
            attribute "device.colorTemperature​$n", "enum", [{device.colorTemperature}.value$]
            command "white$n"
            command "color$n"
            attribute "hue$n", "enum", [{bulbHUE}.value$]
            attribute "saturation$n", "enum", [{bulbSATURATION}.value$]
		}
        
        simulator {

	}

	tiles(scale: 2) {
		multiAttributeTile(name:"switch", type: "lighting", width: 6, height: 4, canChangeIcon: true){
			tileAttribute ("device.switch", key: "PRIMARY_CONTROL") {
				attributeState "on", label:'${name}', action:"switch.off", icon:"http://hosted.lifx.co/smartthings/v1/196xOn.png", backgroundColor:"#79b821", nextState:"turningOff"
				attributeState "off", label:'${name}', action:"switch.on", icon:"http://hosted.lifx.co/smartthings/v1/196xOff.png", backgroundColor:"#ffffff", nextState:"turningOn"
				attributeState "turningOn", label:'Turning on', action:"switch.off", icon:"http://hosted.lifx.co/smartthings/v1/196xOn.png", backgroundColor:"#79b821", nextState:"turningOff"
				attributeState "turningOff", label:'Turning off', action:"switch.on", icon:"http://hosted.lifx.co/smartthings/v1/196xOff.png", backgroundColor:"#ffffff", nextState:"turningOn"
				attributeState "offline", label:'Offline', action:"refresh", icon:"http://hosted.lifx.co/smartthings/v1/196xOff.png", backgroundColor:"#FF0000"
			}

			tileAttribute ("device.level", key: "SLIDER_CONTROL") {
				attributeState "level", action:"switch level.setLevel"
			}

			tileAttribute ("device.colorTemperature", key: "COLOR_CONTROL") {
				attributeState "colorTemperature", action:"device colorTemperature.${currentValue}"
			}

			tileAttribute ("device.model", key: "SECONDARY_CONTROL") {
				attributeState "model", label: '${currentValue}'
			}
		}

		standardTile("refresh", "device.switch", inactiveLabel: false, decoration: "flat", width: 2, height: 2) {
			state "default", label:"", action:"refresh.refresh", icon:"st.secondary.refresh"
		}

		valueTile("null", "device.switch", inactiveLabel: false, decoration: "flat") {
			state "default", label:''
		}

		controlTile("colorTempSliderControl", "device.colorTemperature", "slider", height: 2, width: 4, inactiveLabel: false, range:"(2700..9000)") {
			state "colorTemp", action:"color temperature.setColorTemperature"
		}

		valueTile("colorTemp", "device.colorTemperature", inactiveLabel: false, decoration: "flat", height: 2, width: 2) {
			state "colorTemp", label: '${currentValue}K'
		}

		main "switch"
		details(["switch", "colorTempSliderControl", "colorTemp", "refresh"])
	}

void installed() {
	sendEvent(name: "DeviceWatch-Enroll", value: "{\"protocol\": \"cloud\", \"scheme\":\"untracked\", \"hubHardwareId\": \"${device?.hub?.hardwareID}\"}")
    sendEvent(name: "DeviceWatch-Enroll", value: "{\"protocol\": \"lan\", \"scheme\":\"untracked\", \"hubHardwareId\": \"${device?.hub?.hardwareID}\"}")
}

// handle commands
def setHue(percentage) {
	log.debug "setHue ${percentage}"
	parent.logErrors(logObject: log) {
		def resp = parent.apiPUT("/lights/${selector()}/state", [color: "hue:${percentage * 3.6}", power: "on"])
		if (resp.status < 300) {
			sendEvent(name: "hue", value: percentage)
			sendEvent(name: "switch", value: "on")
		} else {
			log.error("Bad setHue result: [${resp.status}] ${resp.data}")
		}
	}
	return []
}

def setSaturation(percentage) {
	log.debug "setSaturation ${percentage}"
	parent.logErrors(logObject: log) {
		def resp = parent.apiPUT("/lights/${selector()}/state", [color: "saturation:${percentage / 100}", power: "on"])
		if (resp.status < 300) {
			sendEvent(name: "saturation", value: percentage)
			sendEvent(name: "switch", value: "on")
		} else {
			log.error("Bad setSaturation result: [${resp.status}] ${resp.data}")
		}
	}
	return []
}

def setColor(Map color) {
	log.debug "setColor ${color}"
	def attrs = []
	def events = []
	color.each { key, value ->
		switch (key) {
			case "hue":
				attrs << "hue:${value * 3.6}"
				events << createEvent(name: "hue", value: value)
				break
			case "saturation":
				attrs << "saturation:${value / 100}"
				events << createEvent(name: "saturation", value: value)
				break
			case "colorTemperature":
				attrs << "kelvin:${value}"
				events << createEvent(name: "colorTemperature", value: value)
				break
		}
	}
	parent.logErrors(logObject:log) {
		def resp = parent.apiPUT("/lights/${selector()}/state", [color: attrs.join(" "), power: "on"])
		if (resp.status < 300) {
			if (color.hex)
				sendEvent(name: "color", value: color.hex)
			sendEvent(name: "switch", value: "on")
			events.each { sendEvent(it) }
		} else {
			log.error("Bad setColor result: [${resp.status}] ${resp.data}")
		}
	}
	return []
}

def setLevel(percentage) {
	log.debug "setLevel level: ${percentage}"
	if (percentage < 1 && percentage > 0) {
		percentage = 1 // clamp to 1%
	}
	if (percentage == 0) {
		return off() // if the brightness is set to 0, just turn it off
	}
	parent.logErrors(logObject:log) {
		def resp = parent.apiPUT("/lights/${selector()}/state", ["brightness": percentage / 100, "power": "on"])
		if (resp.status < 300) {
			sendEvent(name: "level", value: percentage)
			sendEvent(name: "switch.setLevel", value: percentage)
			sendEvent(name: "switch", value: "on")
		} else {
			log.error("Bad setLevel result: [${resp.status}] ${resp.data}")
		}
	}
	return []
}

def setLevel(percentage, rate) {
	log.debug "setLevel level: ${percentage} rate: ${rate} ms"
	if (percentage < 1 && percentage > 0) {
		percentage = 1 // clamp to 1%
	}
	if (percentage == 0 && rate == 0) {
		return off() // if the brightness is set to 0, just turn it off
	}	

	parent.logErrors(logObject:log) {
		def resp = parent.apiPUT("/lights/${selector()}/state", ["brightness": percentage / 100, "duration": (rate / 1000), "power": "on"])
		if (resp.status < 300) {
			if (rate < 5000) {
				sendEvent(name: "level", value: percentage)
				sendEvent(name: "switch.setLevel", value: percentage)
				sendEvent(name: "switch", value: "on")
			} else {
				def refreshSecs = ((rate/1000) + 1)
				log.debug "Scheduling a refresh in " + refreshSecs + " seconds"
				runIn(refreshSecs, refresh, [overwrite: true])
			}
		} else {
			log.error("Bad setLevel result: [${resp.status}] ${resp.data}")
		}
	}
	return []
}

def setColorTemperature(kelvin) {
	log.debug "Executing 'setColorTemperature' to ${kelvin}"
	parent.logErrors() {
		def resp = parent.apiPUT("/lights/${selector()}/state", [color: "kelvin:${kelvin}", power: "on"])
		if (resp.status < 300) {
			sendEvent(name: "colorTemperature", value: kelvin)
			sendEvent(name: "color", value: "#ffffff")
			sendEvent(name: "saturation", value: 0)
		} else {
			log.error("Bad setLevel result: [${resp.status}] ${resp.data}")
		}

	}
	return []
}

def on() {
	log.debug "Device setOn"
	parent.logErrors() {
		if (parent.apiPUT("/lights/${selector()}/state", [power: "on"]) != null) {
			sendEvent(name: "switch", value: "on")
		}
	}
	return []
}

def off() {
	log.debug "Device setOff"
	parent.logErrors() {
		if (parent.apiPUT("/lights/${selector()}/state", [power: "off"]) != null) {
			sendEvent(name: "switch", value: "off")
		}
	}
	return []
}

def refresh() {
	log.debug "Executing 'refresh'"
	
	def resp = parent.apiGET("/lights/${selector()}")
    def data = resp.data[0]
	log.debug("Data: ${data}")

	sendEvent(name: "label", value: data.label)
	sendEvent(name: "level", value: Math.round((data.brightness ?: 1) * 100))
	sendEvent(name: "switch.setLevel", value: Math.round((data.brightness ?: 1) * 100))
	sendEvent(name: "switch", value: data.power)
	sendEvent(name: "color", value: colorUtil.hslToHex((data.color.hue / 3.6) as int, (data.color.saturation * 100) as int))
	sendEvent(name: "hue", value: data.color.hue / 3.6)
	sendEvent(name: "saturation", value: data.color.saturation * 100)
	sendEvent(name: "colorTemperature", value: data.color.kelvin)
	sendEvent(name: "model", value: data.product.name)
    
	if (resp.status == 404) {
		state.online = false
		sendEvent(name: "DeviceWatch-DeviceStatusUpdate", value: "offline", displayed: false)
 		log.warn "$device is Offline"
		sendEvent(name: "switch", value: "offline")
		return []
	} else if (resp.status != 200) {
		log.error("Unexpected result in refresh(): [${resp.status}] ${resp.data}")
		return []
	}
    
	if (data.connected) {
		sendEvent(name: "DeviceWatch-DeviceStatus", value: "online", displayed: false)
		log.debug "$device is Online"
	} else {
		sendEvent(name: "DeviceWatch-DeviceStatus", value: "offline", displayed: false)
		log.warn "$device is Offline"
		sendEvent(name: "switch", value: "offline")
	}
}

def selector() {
	if (device.deviceNetworkId.contains(":")) {
		return device.deviceNetworkId
	} else {
		return "id:${device.deviceNetworkId}"
	}
}