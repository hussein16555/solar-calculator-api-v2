from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List
import math

app = FastAPI(title='Solar Energy Prediction & Sizing API', version='2.0.0')

class Appliance(BaseModel):
    name: str
    watts: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    hours_per_day: float = Field(gt=0, le=24)
    start_hour: int = Field(default=0, ge=0, le=23)
    end_hour: int = Field(default=23, ge=0, le=23)

class SolarRequest(BaseModel):
    appliances: List[Appliance]
    peak_sun_hours: float = Field(default=5, gt=0, le=12)
    system_voltage: float = Field(default=24, gt=0)
    battery_dod: float = Field(default=.8, gt=0, le=1)
    system_efficiency: float = Field(default=.8, gt=0, le=1)
    autonomy_days: float = Field(default=1, gt=0)
    inverter_safety_factor: float = Field(default=1.25, gt=0)

def hourly_prediction(appliances):
    out=[]
    for h in range(24):
        power=0; active=[]
        for a in appliances:
            # Supports normal and overnight schedules. 24 as end is treated as midnight.
            if a.start_hour <= a.end_hour:
                on = a.start_hour <= h < a.end_hour
            else:
                on = h >= a.start_hour or h < a.end_hour
            if on:
                power += a.watts*a.quantity; active.append(a.name)
        out.append({'hour':f'{h:02d}:00','hour_number':h,'predicted_power_w':round(power,2),
                    'predicted_energy_wh':round(power,2),'active_equipment':active})
    return out

def calculate(req):
    daily_wh=sum(a.watts*a.quantity*a.hours_per_day for a in req.appliances)
    hourly=hourly_prediction(req.appliances)
    peak=max(hourly,key=lambda x:x['predicted_power_w'])
    peak_load=max(sum(a.watts*a.quantity for a in req.appliances),peak['predicted_power_w'])
    pv=daily_wh/(req.peak_sun_hours*req.system_efficiency)*1.15
    battery_wh=daily_wh*req.autonomy_days/req.battery_dod
    battery_ah=battery_wh/req.system_voltage
    inverter=peak_load*req.inverter_safety_factor
    pv_rec=math.ceil(pv/100)*100; batt_rec=math.ceil(battery_ah/10)*10; inv_rec=math.ceil(inverter/100)*100
    return {'daily_energy_wh':round(daily_wh,2),'daily_energy_kwh':round(daily_wh/1000,2),
      'peak_load_w':round(peak_load,2),
      'solar_panel':{'recommended_total_w':pv_rec,'example_panels_550w':math.ceil(pv_rec/550)},
      'battery':{'required_wh':round(battery_wh,2),'required_ah':round(battery_ah,2),'recommended_ah_at_system_voltage':batt_rec,'system_voltage_v':req.system_voltage},
      'inverter':{'recommended_w':inv_rec,'recommended_kw':round(inv_rec/1000,2)},
      'hourly_prediction':hourly,
      'prediction_summary':{'predicted_peak_hour':peak['hour'],'predicted_peak_power_w':peak['predicted_power_w'],
                            'scheduled_hourly_energy_kwh':round(sum(x['predicted_energy_wh'] for x in hourly)/1000,2),
                            'note':'Schedule-based hourly forecast'}}

@app.get('/api/health')
def health(): return {'status':'ok','version':'2.0.0'}

@app.post('/api/calculate')
def calculate_solar(req: SolarRequest): return calculate(req)

@app.post('/api/predict-hourly')
def predict_hourly(req: SolarRequest):
    r=calculate(req)
    return {'hourly_prediction':r['hourly_prediction'],'peak_hour':r['prediction_summary']['predicted_peak_hour'],
            'peak_power_w':r['prediction_summary']['predicted_peak_power_w'],
            'total_scheduled_energy_kwh':r['prediction_summary']['scheduled_hourly_energy_kwh']}

app.mount('/',StaticFiles(directory='static',html=True),name='static')
