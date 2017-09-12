import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-west-1:845784170256:deployPortfolioTopic')

    s3 = boto3.resource('s3')

    try:
        portfolio_bucket = s3.Bucket('portfolio.thegymio.com')
        build_bucket = s3.Bucket('portfoliobuild.thegymio.com')

        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                content_type = {'ContentType': mimetypes.guess_type(nm)[0]}
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs=content_type)
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print 'Job done!'
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed successfully!")
    except:
        topic.publish(Subject="Portfolio Deploy Failed", Message="The Portfolio was not deployed successfully")
        raise

    return 'Hello from Lambda'
