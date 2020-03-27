# Lambda functions

basically directory name is same as function name

## how to update layer
show how to update slack layer as example

1. run `cd package && ./make_zip.sh` -> `sg.zip` is created in `~/Downloads`
2. Go to https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/layers
3. Select "slack" -> "Create version"
4. Upload `sg.zip`
5. Click "Create"
