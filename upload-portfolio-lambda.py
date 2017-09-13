import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-west-1:845784170256:deployPortfolioTopic')

    location = {
        "bucketName": 'portfoliobuild.thegymio.com',
        "objectKey": 'portfoliobuild.zip'
    }

    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print "Building portfolio from " + str(location)

        portfolio_bucket = s3.Bucket('portfolio.thegymio.com')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                content_type = {'ContentType': mimetypes.guess_type(nm)[0]}
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs=content_type)
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print 'Job done!'
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed successfully!")

        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="Portfolio Deploy Failed", Message="The Portfolio was not deployed successfully")
        raise

    return 'Hello from Lambda'
