# Importing the dependencies
import time
import boto3
import nltk
from nltk.stem.porter import PorterStemmer
import pypandoc

class Resume:
    
    # Attributes of the resume. 
 
    name='Not Found'
    age = 'Not Found'
    gender = 'Not Found'
    dob = 'Not Found'
    address = 'Not Found'
    chief_medical_complaint = 'Not Found'
    current_date = ''
    symptoms = []
    allergies = []
    vital_signs = {}
    medications = []
    entity_list = []

    s3 = boto3.client('s3')
    comprehend = boto3.client('comprehendmedical')
    dynamodb = boto3.resource('dynamodb')
    
    def __init__(self,raw_resume_text):

        date = time.localtime()
        self.current_date = time.strftime("%Y-%m-%d", date)
        self.entity_list = self.comprehend.detect_entities(Text = raw_resume_text)['Entities']
        
        # Initailizing name
        for entity in self.entity_list:
            if entity['Type'] =='Name':
                self.name = entity['Text']
                break
        
        # Initailizing age
        for entity in self.entity_list:
            if entity['Type'] =='AGE':
                age = entity['Text']
                break
        
        # Initailizing gender
        if ' female ' in raw_resume_text.lower():
            self.gender = 'Female'
        elif ' male ' in raw_resume_text.lower():
            self.gender = 'Male'
        
        for entity in self.entity_list:
            if entity['Type']=='DATE':
                S = raw_resume_text[max(entity['BeginOffset']-10,0):entity['EndOffset']+1]
                if S.find('DOB')!=-1 or S.find('D.O.B.')!=-1 or S.find('Birth')!=-1:
                    self.dob = entity['Text']
        
        
        # Initailizing address
        address = ''
        for entity in self.entity_list:
            if entity['Type']=='ADDRESS':
                address += entity['Text']+', '
        if address !='':
             self.address = address[:-2]
        
        
        # Initailizing symptoms

        porter_stemmer = PorterStemmer()
        SymptomList = []
        StemSymList = []
        for entity in self.entity_list:
            if len(entity['Traits']) == 1 and entity['Traits'][0]['Name'] == 'SYMPTOM':
                symptom = entity['Text']
                stemmed_symptom = porter_stemmer.stem(symptom)
                if stemmed_symptom not in StemSymList :                                  
                    SymptomList.append(symptom.capitalize())
                    StemSymList.append(stemmed_symptom)           
        if len(SymptomList)!=0:
            self.chief_medical_complaint = SymptomList[0]
        self.symptoms = SymptomList
        
        
        # Initailizing allergies
        allergies = []
        for entity in self.entity_list:
            if ((entity['Type'] == 'BRAND_NAME' or entity['Type'] == 'GENERIC_NAME') and \
                len(entity['Traits'])!=0 and entity['Traits'][0]['Name']=='NEGATION'):
                allergies.append(entity['Text'])
        self.allergies = allergies        
                
        # Initailizing medications
        medications = []
        for entity in self.entity_list:
            medication = {'Generic_name':'NF','Strength':'NF','Dosage':'NF','Form':'NF','Route_or_mode':'NF','Frequency':'NF'} 
            if (entity['Type'] == 'GENERIC_NAME' or entity['Type'] == 'BRAND_NAME') and 'Attributes' in entity:
                medication['Generic_name'] = entity['Text']
                for attribute in entity['Attributes']:
                    medication[attribute['Type'].capitalize()] = attribute['Text']
                
                medications.append(medication)
        self.medications = medications
        
        # Initailizing vital signs
        self.vital_signs = {'Found':[],'Negated':[]}
        for entity in self.entity_list:
            if entity['Category']=='MEDICAL_CONDITION' and len(entity['Text'].split(' '))>1:
                if len(entity['Traits'])== 1 and entity['Traits'][0]['Name']== 'SIGN':
                    self.vital_signs['Found'].append(entity['Text'])
    
                if ((len(entity['Traits'])== 2 and entity['Traits'][0]['Name']== 'SIGN' and \
                    entity['Traits'][1]['Name']== 'NEGATION')):
                    self.vital_signs['Negated'].append(entity['Text'])
        
        
        # Initailizing medical_tests
        TEST = []
        self.medical_tests =  []       
        for entity in self.entity_list:
            if entity['Type'] == 'TEST_NAME' and 'Attributes' in entity and \
                len(entity['Attributes'])>0 and entity['Text'].lower() not in TEST :
                medical_test = {'Test_name':'','Test_value':''}
                TEST.append(entity['Text'].lower())
                medical_test['Test_name'] = entity['Text'].capitalize()
                for test in entity['Attributes']:
                    medical_test['Test_value'] += test['Text'] + ' '
                self.medical_tests.append(medical_test)
         
                
                
                
    # Generating the Medical Resume   
    def make_resume(self):
        htmlcode = '<font color="#b30000"><H1 align="center">Patient Information</H1></font>'

        htmlcode += '<b>Name : </b>' + self.name+'<br><br>'   
        
        htmlcode += '<b>Age : </b>' + str(self.age)+'<br><br>'
        
        htmlcode += '<b>Gender : </b>' + self.gender + '<br><br>'
        
        htmlcode += '<b>DOB : </b>' + self.dob + '<br><br>'
        
        htmlcode += '<b>Address : </b>' + self.address + '<br><br>'
        
        htmlcode += '<b>Time of Visit : </b>' + self.current_date + '<br><br>'
        
        htmlcode += '<b>Chief Medical Complaint : </b>' + self.chief_medical_complaint +'<br><br>'
        
        htmlcode += '<b>Symptoms : </b><br><br><table><tr>'
        for i in range(len(self.symptoms)):
            htmlcode += '<td><ul><li>'+self.symptoms[i] + '</li></ul></td>'
            if (i+1)%4 == 0 or i == len(self.symptoms)-1:
                htmlcode += '</tr>'
                if i != len(self.symptoms)-1:
                    htmlcode += '<tr>'
        htmlcode += '</table>' + (' <br>'*3) + '<b>Allergies : </b>'
        
        htmlcode += str(self.allergies)[1:-1].replace("'",'') + '<br><br>'
        
        htmlcode += '<b>Vital Signs : </b><br><ul>'
        htmlcode += '<li>Found : ' + str(self.vital_signs['Found'])[1:-1].replace("'",'') + '</li><br>'
        htmlcode += '<li>Negated : ' + str(self.vital_signs['Negated'])[1:-1].replace("'",'') + '</li></ul><br>'
        
        
        attributes = {'Generic_name','Strength','Dosage','Form','Route_or_mode','Frequency'}
        htmlcode += '<b>Medications : </b><br><table><tr>'
        for attribute in attributes:
            htmlcode += '<th><b>'+attribute+'</b></th>'
        htmlcode += '</tr>'
        for medication in self.medications:
            htmlcode += '<tr>'
            for key in medication:
                htmlcode += '<td>' + medication[key] + '</td>'
            htmlcode += '</tr>'
        htmlcode += '</table><br><br>'
        
 
        htmlcode += '<b>Medical Tests : </b><br><ul>'
        for test in self.medical_tests:
            htmlcode += '<li>' + test['Test_name'] + ' : ' + test['Test_value'] + '</li>' 
        htmlcode += '</ul>'
        return htmlcode

    def save_to_ehr(self,table_name,bucket_name,key):
        
        htmlcode = self.make_resume()
        html_key = f'MedicalResume/HTML/{key}_{self.current_date}.html'
        doc_key = f'MedicalResume/DOCX/{key}_{self.current_date}.docx'

        # Saving html file to disk
        html_file = open('/tmp/resume.html',"w").write(htmlcode)
        #pypandoc.convert_file('/tmp/resume.html', 'docx', outputfile="/tmp/resume.docx")

        # saving html and docx file to s3 bucket
        self.s3.put_object(Bucket = bucket_name, Key = html_key, Body = open('/tmp/resume.html',"rb"))
        #self.s3.put_object(Bucket = bucket_name, Key = doc_key, Body = open('/tmp/resume.docx',"rb"))
        
        table = self.dynamodb.Table(table_name)
        response = table.put_item(
            Item = {
                'NAME' : self.name,
                'DATE' : self.current_date,
                'AGE' : self.age,
                'GENDER' : self.gender,
                'DOB' : self.dob,
                'ADDRESS' : self.address,
                'CHIEF_MEDICAL_COMPLAINT' : self.chief_medical_complaint,
                'SYMPTOMS' : self.symptoms,
                'ALLERGIES' : self.allergies,
                'VITAL_SIGNS' : self.vital_signs,
                'MEDICATIONS' : self.medications,
                'MEDICAL_NOTES' : self.medical_tests,
                'RESUME_LINK' : f's3://{bucket_name}/{html_key}'
        }
        )
