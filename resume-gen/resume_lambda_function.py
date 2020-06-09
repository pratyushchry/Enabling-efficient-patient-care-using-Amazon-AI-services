import json
import boto3
from util import Resume 

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    transcribe = boto3.client('transcribe')
    
    job_name = event["detail"]["TranscriptionJobName"]
    response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    transcript_uri = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    transcript_bucket = transcript_uri.split("/")[-2]
    transcript_key = transcript_uri.split("/")[-1]
    file_name = job_name.split("-")[-1]                 # extract input file name from transcript name
    
    obj = s3_resource.Object(transcript_bucket,transcript_key).get()["Body"].read()
    transcript = json.loads(obj)
    raw_resume_text = transcript["results"]["transcripts"][0]["transcript"]
    
    table_name = "Electronic-Health-Records"
    resume_bucket = "comprehend-medical-asa"
    
    myresume = Resume(raw_resume_text)
    myresume.save_to_ehr(table_name,resume_bucket,file_name)