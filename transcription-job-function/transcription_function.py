import json
import boto3

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    transcribe = boto3.client("transcribe")
    
    file = event["Records"][0]
    bucket_name = str(file["s3"]["bucket"]["name"])
    key = str(file["s3"]["object"]["key"])
    file_name = key.split("/")[-1].split(".")[0]
    job_name = context.aws_request_id
    file_url = f's3://{bucket_name}/{key}'
    
    transcribe.start_transcription_job(TranscriptionJobName = job_name+"-"+file_name,
                                        Media = {"MediaFileUri":file_url},
                                        MediaFormat = "mp3",
                                        LanguageCode = "en-US",
                                        OutputBucketName = "comprehend-medical-transcription-job"
                                        )
                                        
    
