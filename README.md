# Dam Dash

Plotly Dash (Flask) web app for looking at some dam levels.

## How to deploy on a windows server using IIS

If you're unfortunate enough to have to deploy a Dash app on a Windows server, here's how you can do it.

### Clone the repo.
First you need to put the file where IIS can see it. I find it easiest to put it in the `wwwroot` folder. This is usually located in `C:\inetpub\wwwroot`. In my case I wasn't able to clone the repository directly into the `wwwroot` folder because I didn't have the permissions to do so. So I cloned the repository into a different folder and then copied the files into the `wwwroot` folder.

Once you have your files in the `wwwroot` folder, we need to tell IIS how  to run this app. We do that by making a file called `web.config` in the root of the app. The `web.config` file should look something like this:

```xml

```

### Install Python and the required packages.
Assuming you have the necessary permissions, you can install Python. I used Python 3.12, but anything later than 3.6 should work. You can download Python from the [official website](https://www.python.org/downloads/).

### Create the virtual environment.
We need to create a virtual environment for the app to run in. You can do this by running the following command in the command prompt:
```bash
python3 -m venv /path/to/venv
```

You can activate the virtual environment by running the following command:
```bash
source /path/to/venv/Scripts/activate
```

### Install the required packages.
With an activated venv you can install the required packages by running the following command:
```bash
pip install -r requirements.txt
```

## Now on the IIS side of things.
For the most part I used this guide to set all of this up: https://medium.com/@b-nouri/how-to-deploy-your-dash-app-on-iis-windows-server-98a16b8707e1



