import json, logging, os, glob,base64,time,subprocess

from pathlib import Path
from requests import Session
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox,FirefoxProfile
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,NoSuchElementException

from rest_framework.permissions import IsAuthenticated 
from django.views import View
from django.http import HttpResponse

from app.models import Log,Errors

from .models import ClienteDTE

logger=logging.getLogger(__file__)

BASE_DIR=Path(__file__).parent.parent.resolve()
files_path=os.path.join(BASE_DIR,'data/')

def check_status(rut):
    try:
        cliente=ClienteDTE.objects.filter(rut=rut)
        estado=cliente[0].Estado
        if not estado:
            return 'No tiene acceso'
        else:
            return None
    except:
        return 'No tiene acceso'

def login(rut_cliente):
    rut,dv= rut_cliente.split('-')
    url_inicio='https://zeusr.sii.cl//AUT2000/InicioAutenticacion/IngresoRutClave.html?https://misiir.sii.cl/cgi_misii/siihome.cgi'

    logger.info(msg='login de usuario:'+rut_cliente )
    try:
        company = ClienteDTE.objects.filter(rut=rut_cliente)    
        cert_path = company[0].certificate.path
        install_path = os.path.join(BASE_DIR,'data/Install_certificate.sh')
        # print(install_path)
        subprocess.run(['bash', install_path,cert_path,company[0].name])
        # print('La instalacion finalizo con codigo:', cert_install.returncode)
    except:
        response={}
        response['estado']='Error'
        response['msg']='Error al encontrar la compañia o instalar certificados. Compruebe e intente nuevamente'
        return HttpResponse(json.dumps(response))
    try:
    #Probando con requests
        s=Session()
        s.get(url_inicio) 
        url_post = 'https://herculesr.sii.cl/cgi_AUT2000/CAutInicio.cgi?https://misiir.sii.cl/cgi_misii/siihome.cgi'
        s.post(url_post,cert=cert_path, allow_redirects=True, data={'rut' : rut,
                'referencia' : 'https://www.sii.cl',
                'dv': dv})
        time.sleep(1)
        s.get('https://maullin.sii.cl/cvc_cgi/dte/of_solicita_folios')
        cookies=s.cookies 
        s.close()
        return cookies
    except:
        response={}
        response['estado']='Error'
        response['msg']='Error al conseguir las credenciales de acceso SII'
        return HttpResponse(json.dumps(response)) 

class PedirFolios(View):

    permission_classes = (IsAuthenticated,)
    
    def get(self,request):
    
        # RUT, Tipo Documento, Nro de Folios a Timbrar

               
        type_doc = ["33","43","46","56","61"]
        url_inicio ='https://zeusr.sii.cl//AUT2000/InicioAutenticacion/IngresoRutClave.html?https://misiir.sii.cl/cgi_misii/siihome.cgi'
        data = json.loads(request.body)
        

        rut = data['rut']        
        cod_doc = data['cod_doc']
        cant_folios = data['cant_folios']
        ambiente=data['ambiente']
        user=data['user']
        pwd=data['pass']
        if ambiente == 'prod':
            url_folios = 'https://palena.sii.cl/cvc_cgi/dte/of_solicita_folios'
            url_dte = 'http://ldte.opens.cl/usuarios/ingresar'
            url_caf = 'https://ldte.opens.cl/dte/admin/dte_folios/subir_caf'
        elif ambiente == 'cert' :
            url_folios = 'https://maullin.sii.cl/cvc_cgi/dte/of_solicita_folios'
            url_dte = 'http://ldtetest.opens.cl/usuarios/ingresar'
            url_caf = 'https://ldtetest.opens.cl/dte/admin/dte_folios/subir_caf'  
        else:
            response={}
            response['estado']='Error'
            response['msg']='Ambiente incorrecto'
            return HttpResponse(json.dumps(response))

        estado = check_status(rut=rut)
        if estado:
            l = Log(user=rut,msg=' Intenta utilizar servicios sin permisos', service='check_status')
            l.save()
            er = Errors(user=rut,msg=' Intenta utilizar servicios sin permisos', service='check_status')
            er.save()
            logger.info(msg=rut+'-Intenta utilizar servicios sin permisos')
            response={}
            response['estado']='Error'
            response['msg']=estado
            # response['status']= status.HTTP_401_UNAUTHORIZED
            return HttpResponse(json.dumps(response))

        l = Log(user=rut,msg=' solicita '+cant_folios+' folios', service='PedirFoliosDTE')
        l.save()
        logger.info(msg=rut+'-Solicita '+cant_folios+' folios')

        cookies = login(rut_cliente=rut)
        
        firefox_opt = Options() #FirefoxOptions()
        firefox_opt.headless=True
        firefox_prof = FirefoxProfile(profile_directory=os.path.join(files_path,'profile'))
        firefox_prof.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_prof.set_preference("browser.download.folderList",2)
        firefox_prof.set_preference("browser.download.dir", os.path.join(files_path,'downloads'))
        firefox_prof.set_preference("browser.download.useDownloadDir", True)
        firefox_prof.set_preference("browser.download.viewableInternally.enabledTypes", "")
        firefox_prof.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "text/xml,application/xml,application/octet-stream")
        driver_path=os.path.join(files_path,'driver/geckodriver')
        rut,dv = rut.split('-')
        try:
            #agregar options para ejecutar en servidor
            driver = Firefox(executable_path=driver_path,firefox_profile=firefox_prof,options=firefox_opt)
            driver.get(url_inicio)
            for cookie in cookies:
                driver.add_cookie({
                    'name': cookie.name,
                    'value': cookie.value,
                    'path': '/',
                    'domain': cookie.domain
                })
            # print('cookies driver post get:\n' , driver.get_cookies(),'\n\n')
            driver.get(url_folios)
                       
            input_rut = WebDriverWait(driver,10).until(EC.element_to_be_clickable ((By.XPATH,'/html/body/form/center/table/tbody/tr/td[2]/input[1]')))
            input_dv = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/form/center/table/tbody/tr/td[2]/input[2]')))
            input_rut.send_keys(str(rut))
            input_dv.send_keys(str(dv))
            driver.find_element(By.NAME,'ACEPTAR').click()                           
        except:
            # driver.close()
            l=Log(user = rut,msg =' Error en el driver,no se aceptan las cookies', service='PedirFoliosDTE')
            l.save()
            er=Errors(user = rut,msg=' Error en el driver,no se aceptan las cookies', service='PedirFoliosDTE')
            er.save()
            logger.info(msg = rut+'-Error en el driver,no se aceptan las cookies')
            response={}
            response['estado']='Error'
            response['msg']='Driver no acepta cookies'
            return HttpResponse(json.dumps(response))
        
        # print('Se solicita el folio')
        try:
            select_doc = Select(WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'COD_DOCTO'))))
            select_doc.select_by_value(cod_doc)
            #Codigos: 33,34,39,41,43,46,52,56,61,110,111,112
            #Codigos con max: 33,43,46,56,61
            if cod_doc in type_doc:
                #El documento elegido tiene maximo de folios
                max_folios = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'MAX_AUTOR'))).get_attribute('value')
                input_cant_folios = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'CANT_DOCTOS')))
                if max_folios < cant_folios:
                    driver.close()
                    l=Log(user = rut,msg =' solicita mas folios del maximo permitido', service='PedirFoliosDTE')
                    l.save()
                    logger.info(msg = rut+'-Solicita mas folios del maximo permitido')
                    er=Errors(user = rut,msg=' solicita mas folios del maximo permitido', service='PedirFoliosDTE')
                    er.save()
                    response={}
                    response['estado']='Error'
                    response['msg']='La cantidad de folios supera el maximo permitido.\n Maximo folios: ' + str(max_folios)
                    return HttpResponse(json.dumps(response))
                else:
                    input_cant_folios.send_keys(str(cant_folios))      
            else:                
                input_cant_folios= WebDriverWait(driver,10).until(EC.presence_of_element_located((By.NAME,'CANT_DOCTOS')))
                input_cant_folios.send_keys(str(cant_folios))
            #Probar si se encuentra alguna alerta o error
            WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'ACEPTAR'))).click()

        except:
            # print('texto')
            text_box=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]')))
            response={}
            response['estado']='Error'
            response['msg'] = text_box.text
            driver.close()
            return HttpResponse(json.dumps(response))
    
        try:
            WebDriverWait(driver,5).until(EC.alert_is_present())
            # print('alerta')
            alert=driver.switch_to.alert
            texto=alert.text
            alert.accept()
            l=Log(user=rut,msg='Se detecto una alerta', service='PedirFoliosDTE')
            l.save()
            er=Errors(user=rut,msg='Se detecto una alerta', service='PedirFoliosDTE')
            er.save()
            logger.info(msg=rut+'-'+ texto)
            response={}
            response['estado']='Error'
            response['msg']=texto
            driver.close()
            return HttpResponse(json.dumps(response)) 

        except TimeoutException:
            # print('descargar xml')
            # cuando la pagina sea la correcta se descarga el archivo
            WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'ACEPTAR'))).click()
            # print('Descargar XML de folio')
            boton_descarga = WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'ACEPTAR')))
            boton_descarga.click() 
            # Retornar archivo
            # print('se descargo el archivo')
            files=glob.glob(os.path.join(files_path,'downloads/*.xml'))
            max_file = max(files,key=os.path.getctime)
            # print(max_file)
            l=Log(user=rut,msg=' Finaliza correctamente', service='PedirFoliosDTE')
            l.save()
            logger.info(msg=rut+'-PedirFolios finaliza correctamente') 
        
        try:
            # Comienza certificacion en libredte
            # print('certificacion dte')
            driver.get(url_dte)
            input_usuario= WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID,'user')))
            input_usuario.send_keys(str(user))
            input_pass=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID,'pass')))
            input_pass.send_keys(str(pwd))
            WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[2]/div/div/div/form/button'))).click()
            
            #elegir empresa segun rut
            WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'//a[@href="seleccionar/'+rut+'"]'))).click()

            driver.get(url_caf)
            upload = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID,'cafField')))
            upload.send_keys(max_file)

            WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.ID,'submitField'))).click()
        except:
            driver.close()
            # print('problema login libredte')
            files=glob.glob(os.path.join(files_path,'downloads/*.xml'))
            max_file = max(files,key=os.path.getctime)
            with open(max_file,'rb') as f:
                data=f.read()
                # print(data)
                b64=base64.encodebytes(data).decode("utf-8")
                b64=b64.replace('\n','')
            response={}
            response['estado']='Error'
            response['msg']='Problemas de login LibreDTE'
            response['xml']= b64
            return HttpResponse(json.dumps(response))

        
        try:
            # alert alert-success class name
            alerta=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[2]')))
            clase = alerta.get_attribute('class')
            texto=alerta.text.split('\n')[-1]
            # print(clase)
            if clase == 'alert alert-danger':
                # print('hubo un error')
                l=Log(user=rut,msg='Se detecto una alerta', service='PedirFoliosDTE')
                l.save()
                er=Errors(user=rut,msg='Se detecto una alerta', service='PedirFoliosDTE')
                er.save()
                logger.info(msg=rut+'-'+ texto)
                response={}
                response['estado']='Error'
                response['msg']=texto
                driver.close()
                return HttpResponse(json.dumps(response))
            elif clase == 'alert alert-success':
                # print('funciono')
                response={}
                response['estado']='OK'
                response['msg']=texto
                l=Log(user=rut,msg='Se finalizo con exito', service='PedirFoliosDTE')
                l.save()
                logger.info(msg=rut+'-'+ texto)
                driver.close()
                return HttpResponse(json.dumps(response))
                            
        except:
            driver.close()
            # print('problema login libredte')
            response={}
            response['estado']='Error'
            response['msg']='Error LibreDTE'
            return HttpResponse(json.dumps(response))