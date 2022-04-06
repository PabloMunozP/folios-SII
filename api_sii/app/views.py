import json, os, time, subprocess,glob, base64

from requests import Session
from pathlib import Path
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import Firefox,FirefoxProfile
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib3 import Retry
import logging

from rest_framework.permissions import IsAuthenticated 
from django.views import View
from django.http import HttpResponse
from .models import Cliente,Log, Errors

logger=logging.getLogger(__file__)

BASE_DIR=Path(__file__).parent.parent.resolve()
files_path=os.path.join(BASE_DIR,'data/')
type_doc = ["33","43","46","56","61"]
# Create your views here.


def check_status(rut):
    try:
        cliente=Cliente.objects.filter(rut=rut)
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
        company = Cliente.objects.filter(rut=rut_cliente)    
        cert_path = company[0].certificate.path
        install_path = os.path.join(BASE_DIR,'data/Install_certificate.sh')
        print(install_path, cert_path)
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


class ViewLog(View):
    def get(self,request):
        logs= Log.objects.all()
        for l in logs:
            print(l.msg)
        return HttpResponse('Ok')

class PedirFolios(View):

    permission_classes = (IsAuthenticated,)
    
    def get(self,request):
    
        # RUT, Tipo Documento, Nro de Folios a Timbrar

        # documentos con maximo       
        
        url_inicio ='https://zeusr.sii.cl//AUT2000/InicioAutenticacion/IngresoRutClave.html?https://misiir.sii.cl/cgi_misii/siihome.cgi'
        data = json.loads(request.body)
        
        rut = data['rut']        
        cod_doc = data['cod_doc']
        cant_folios = data['cant_folios']
        ambiente=data['ambiente']

        if ambiente == 'prod':
            url_folios= 'https://palena.sii.cl/cvc_cgi/dte/of_solicita_folios'
        elif ambiente == 'cert' :
            url_folios = 'https://maullin.sii.cl/cvc_cgi/dte/of_solicita_folios'   
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
            return HttpResponse(json.dumps(response))

        l = Log(user=rut,msg=' solicita '+cant_folios+' folios', service='PedirFolios')
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
            driver.close()
            l=Log(user = rut,msg =' Error en el driver,no se aceptan las cookies', service='PedirFolios')
            l.save()
            er=Errors(user = rut,msg=' Error en el driver,no se aceptan las cookies', service='PedirFolios')
            er.save()
            logger.info(msg = rut+dv+'-Error en el driver,no se aceptan las cookies')
            response={}
            response['estado']='Error'
            response['msg']='Driver no acepta cookies'
            return HttpResponse(json.dumps(response))
        
        # print('Se solicita el folio')
        try:
            select_doc = Select(WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'COD_DOCTO'))))
            select_doc.select_by_value(cod_doc)
            if cod_doc in type_doc:
                #El documento elegido tiene maximo de folios
                max_folios = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'MAX_AUTOR'))).get_attribute('value')
                input_cant_folios = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'CANT_DOCTOS')))
                if max_folios < cant_folios:
                    driver.close()
                    l=Log(user = rut,msg =' solicita mas folios del maximo permitido', service='PedirFolios')
                    l.save()
                    logger.info(msg = rut+'-Solicita mas folios del maximo permitido')
                    er=Errors(user = rut,msg=' solicita mas folios del maximo permitido', service='PedirFolios')
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
            l=Log(user=rut,msg=' Se detecto una alerta', service='PedirFolios')
            l.save()
            er=Errors(user=rut,msg=' Se detecto una alerta' , service='PedirFolios')
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
            files=glob.glob(os.path.join(files_path,'downloads/*.xml'))
            max_file = max(files,key=os.path.getctime)
            with open(max_file,'rb') as f:
                data=f.read()
                # print(data)
                b64=base64.encodebytes(data).decode("utf-8")
                b64=b64.replace('\n','')
            l=Log(user=rut,msg=' Finaliza correctamente', service='PedirFolios')
            l.save()
            logger.info(msg=rut+'-PedirFolios finaliza correctamente')
            driver.close()
            response={}
            response['estado']='Ok'
            response['msg']='Finaliza correctamente'
            response['xml']= b64
            return HttpResponse(json.dumps(response))                          

class AnularFolios(View):
    permission_classes= (IsAuthenticated,)

    def get(self,request):
        # ID Solicitud, Folio Inicial a Anular, Folio Final a Anular, Motivo de la Anulación
        
                
        data=json.loads(request.body)
        folio_inicio= data['folio_inicio']
        folio_final= data['folio_final']
        motivo= data['motivo']
        rut=data['rut']
        id=data["id"]
        cod_doc,id_in,id_fin=id.split('-',maxsplit=3)
        ambiente=data['ambiente']
        if ambiente == 'prod':
            url_anular='https://palena.sii.cl/cvc_cgi/dte/af_anular1'
        elif ambiente == 'cert' :
            url_anular='https://maullin.sii.cl/cvc_cgi/dte/af_anular1' 
        else:
            response={}
            response['estado']='Error'
            response['msg']='Ambiente incorrecto'
            return HttpResponse(json.dumps(response))

        estado=check_status(rut=rut)
        if estado:
            l=Log(user=rut,msg=' Intenta utilizar servicios sin permisos', service='check_status')
            l.save()
            er=Errors(user=rut,msg=' Intenta utilizar servicios sin permisos', service='check_status')
            er.save()
            logger.info(msg=rut+'-Intenta utilizar servicios sin permisos')
            response={}
            response['estado']='Error'
            response['msg']=estado
            return HttpResponse(json.dumps(response))

        l= Log(user=rut,msg=' solicita anular folios'+ folio_inicio+'-'+folio_final , service='AnularFolios')
        logger.info(msg=rut+'-Solicita anular folios ')

        cookies =  login(rut_cliente=rut)
        rut,dv=rut.split('-')
        firefox_opt =Options() #FirefoxOptions()
        firefox_opt.headless=True
        firefox_prof= FirefoxProfile(profile_directory=os.path.join(files_path,'profile'))
        firefox_prof.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_prof.set_preference("browser.download.folderList",2)
        firefox_prof.set_preference("browser.download.dir", os.path.join(files_path,'downloads'))
        firefox_prof.set_preference("browser.download.useDownloadDir", True)
        firefox_prof.set_preference("browser.download.viewableInternally.enabledTypes", "")
        firefox_prof.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "text/xml,application/xml,application/octet-stream")
        driver_path=os.path.join(files_path,'driver/geckodriver')

        try:
            #anular folios
            driver=Firefox(executable_path=driver_path,firefox_profile=firefox_prof,options=firefox_opt)
            driver.get(url_anular)
            for cookie in cookies:
                driver.add_cookie({
                    'name': cookie.name,
                    'value': cookie.value,
                    'path': '/',
                    'domain': cookie.domain
                })
            # print('cookies driver post get:\n' , driver.get_cookies(),'\n\n')
            driver.get(url_anular)
            input_rut=WebDriverWait(driver,5).until(EC.element_to_be_clickable ((By.NAME,'RUT_EMP')))
            input_dv=WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'DV_EMP')))
            input_rut.send_keys(str(rut))
            input_dv.send_keys(str(dv))
            select_doc = Select(WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'COD_DOCTO'))))
            select_doc.select_by_value(cod_doc)
            driver.find_element(By.NAME,'ACEPTAR').click()
        except:
            l=Log(user=rut,msg=' Error en el driver, no se aceptan las cookies', service='AnularFolios')
            l.save()
            logger.info(msg=rut+'-Error en el driver, no se aceptan las cookies')
            response={}
            response['estado']='Error'
            response['msg']='Driver no acepta cookies'
            return HttpResponse(json.dumps(response))
            # return Response('No se aceptan las cookies',status=status.HTTP_500_INTERNAL_SERVER_ERROR)      

        
        bool_button = False
              
        try:    
            while not bool_button:
                #Revisar la tabla de folios para anular
                table = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[3]/table')))
                data = table.find_elements(By.TAG_NAME,'tr')
                #Separar en segun espacios
                split=data[0].text.split(' ',maxsplit=6)
                i=1
                for tr in data[1:]:
                #buscar cual es la linea con lo solicitado
                #puede haber mas de 1 pagina
                    resp = tr.text.split(' ',maxsplit=4)
                    # print(resp)
                    tr_folioI=resp[2]
                    tr_folioF=resp[3]
                    if tr_folioI == id_in and tr_folioF == id_fin:
                        bool_button = True
                        select_button = WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'MOD'+str(i))))
                        select_button.click()
                        input_folio_ini=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'FOLIO_INI_A')))
                        input_folio_ini.clear()
                        # print(folio_inicio)
                        input_folio_ini.send_keys(str(folio_inicio))

                        input_folio_fin=WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'FOLIO_FIN_A')))
                        input_folio_fin.clear()
                        # print(folio_final)
                        input_folio_fin.send_keys(str(folio_final))
                        
                        input_motivo= WebDriverWait(driver,5).until(EC.presence_of_element_located((By.NAME,'MOTIVO')))
                        input_motivo.send_keys(str(motivo))

                        enviar=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.NAME,'ACEPTAR')))
                        enviar.click()
                    
                        WebDriverWait(driver,5).until(EC.alert_is_present())
                        alert=driver.switch_to.alert
                        alert.accept()
                        comprobante = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/table/tbody/tr/td/table/tbody')))

                        l=Log(user=rut,msg=' Logro anular los folios '+folio_inicio+'-'+folio_final , service='AnularFolios')
                        l.save()
                        logger.info(msg=rut+'-Logro anular los folios '+folio_inicio+'-'+folio_final)
                        
                        response = {}
                        response['estado'] = 'Ok'
                        response['msg'] = 'Se anulan los folios'
                        response['comprobante'] = comprobante.text
                        driver.close()
                        return HttpResponse(json.dumps(response))
                        # return Response(resp ,status.HTTP_200_OK)
                    i += 1

                nxt= WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.NAME,'NEXT')))
                nxt.click()

        except TimeoutException:
            try:
                print('No se pudo anular los folios')
                texto_titulo = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/table/tbody/tr/td/p/font')))
                texto = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[3]/table/tbody/tr/td/font')))
                response={}
                response['estado']='Error'
                response['msg']='No fue posible anular los folios. Compruebe e intente nuevamente'#texto_titulo.text +' '+ texto.text
                driver.close()
                l=Log(user=rut,msg=' No fue posible anular los folios', service='AnularFolios')
                l.save()
                logger.info(msg=rut+'-No fue posible anular los folios')
                return HttpResponse(json.dumps(response))
                # return Response(resp ,status.HTTP_404_NOT_FOUND)
            except:
                texto = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/table[1]')))
                l=Log(user=rut,msg=' El folio solicitado ya fue anulado', service='AnularFolios')
                l.save()
                logger.info(msg=rut+'-El folio solicitado ya fue anulado')
                response={}
                response['estado']='Error'
                response['msg']=texto.text
                driver.close()
                return HttpResponse(json.dumps(response))
                # return Response(resp,status.HTTP_200_OK)
                               
class ConsultarFolio(View):
    permission_classes= (IsAuthenticated,)

    # renderer_classes = [TemplateHTMLRenderer]
    def get(self,request):
        # RUT, Tipo de Documento
        
        data=json.loads(request.body)
        cod_doc=data['cod_doc']
        rut=data['rut']

        ambiente=data['ambiente']
        if ambiente == 'prod':
            url_consulta='https://palena.sii.cl/cvc_cgi/dte/of_consulta_folios'
        elif ambiente == 'cert' :
            url_consulta='https://maullin.sii.cl/cvc_cgi/dte/of_consulta_folios'   
        else:
            response={}
            response['estado']='Error'
            response['msg']='Ambiente incorrecto'
            return HttpResponse(json.dumps(response))
        estado=check_status(rut=rut)
        if estado:
            l=Log(user=rut,msg=' Intenta utilizar servicios sin permisos', service='check_status')
            l.save()
            logger.info(msg=rut+'-Intenta utilizar servicios sin permisos')
            response={}
            response['estado']='Error'
            response['msg']=estado
            return HttpResponse(json.dumps(response))

        l= Log(user=rut,msg=' inicia consulta folios', service='ConsultaFolios')
        logger.info(msg=rut+'-Consulta folios')

        cookies =  login(rut_cliente=rut)
        rut,dv=rut.split('-')
        firefox_opt =Options() #FirefoxOptions()
        firefox_opt.headless=True
        firefox_prof= FirefoxProfile(profile_directory=os.path.join(files_path,'profile'))
        firefox_prof.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_prof.set_preference("browser.download.folderList",2)
        firefox_prof.set_preference("browser.download.dir", os.path.join(files_path,'downloads'))
        firefox_prof.set_preference("browser.download.useDownloadDir", True)
        firefox_prof.set_preference("browser.download.viewableInternally.enabledTypes", "")
        firefox_prof.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "text/xml,application/xml,application/octet-stream")
        driver_path=os.path.join(files_path,'driver/geckodriver')

        try:
            driver=Firefox(executable_path=driver_path,firefox_profile=firefox_prof,options=firefox_opt)
            driver.get(url_consulta)
            for cookie in cookies:
                driver.add_cookie({
                    'name': cookie.name,
                    'value': cookie.value,
                    'path': '/',
                    'domain': cookie.domain
                })
            # print('cookies driver post get:\n' , driver.get_cookies(),'\n\n')
            driver.get(url_consulta)
            input_rut=WebDriverWait(driver,10).until(EC.element_to_be_clickable ((By.NAME,'RUT_EMP')))
            input_dv=WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.NAME,'DV_EMP')))
            input_rut.send_keys(str(rut))
            input_dv.send_keys(str(dv))
            select_doc = Select(WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.NAME,'COD_DOCTO'))))
            select_doc.select_by_value(cod_doc)
            driver.find_element(By.NAME,'ACEPTAR').click()
        except:
            l=Log(user=rut,msg=' Error en el driver,no se aceptan las cookies', service='ConsultaFolios')
            l.save()
            logger.info(msg=rut+'-Error en el driver,no se aceptan las cookies')
            response={}
            response['estado']='Error'
            response['msg']='Driver no acepta cookies'
            return HttpResponse(json.dumps(response))
            # return HttpResponse('No se aceptan las cookies',status.HTTP_500_INTERNAL_SERVER_ERROR)

        dict_response={}    
                   
        try:
            while True:
                
                table = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/form/table/tbody')))
                data = table.find_elements(By.TAG_NAME,'tr')
                data_split = data[0].text.split(' ')
                for d in data[1:]:
                    resp=d.text.split(' ',maxsplit=4)
                    # print(resp)
                    dict_response[str(cod_doc)+'-'+str(resp[2])+'-'+str(resp[3])] = { str(data_split[0]) : str(resp[0]) , 
                    data_split[1]  :  resp[1],
                    data_split[2] +' '+ data_split[3] :resp[2] , 
                    data_split[4] +' '+ data_split[5] : resp[3],
                    data_split[6]  : resp[4] }
                
                nxt = WebDriverWait(driver,1).until(EC.element_to_be_clickable((By.NAME,'NEXT')))
                nxt.click()

        except TimeoutException:
            if dict_response:
                #si finalizo el try y retorna algo entonces existe tabla y hay que retornar
                l=Log(user=rut,msg=' Finaliza la consulta correctamente', service='ConsultaFolios')
                l.save()
                logger.info(msg=rut+'-Finaliza la consulta correctamente')
                # print(dict_response)
                # response=json.dumps(dict_response)
                response={}
                response['estado']='Ok'
                response['msg']='Finaliza la consulta'
                response['folios']=dict_response
                driver.close()
                return HttpResponse(json.dumps(response))
                # return Response(data=response,status=status.HTTP_200_OK)
            else:
                #finalizo el try sin encontrar informacion, se retorna el texto en pantalla
                # print('No existe informacion')
                texto_titulo = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/table/tbody/tr/td/p/font')))
                texto = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.XPATH,'/html/body/center[2]/form/table/tbody/tr/td/font')))
                response={}
                response['estado']='Error'
                response['msg']=texto_titulo.text +':'+texto.text
                driver.close()
                l=Log(user=rut,msg=' No existe informacion con los datos entregados', service='ConsultaFolios')
                l.save()
                logger.info(msg=rut+'-No existe informacion con los datos entregados')
                
                return HttpResponse(json.dumps(response))
                # return Response(resp,status.HTTP_204_NO_CONTENT)
        
        