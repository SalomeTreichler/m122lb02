# Documentation "Payment System"

By Kian Gribi (TBZ, M122, LB02)

Der Code inklusive inline code Dokumentation kann auf [GitHub/kiangribi](https://github.com/kiangribi/m122_lb02) gefunden werden.

## Usage

| Description                      | Command                                                      |
| -------------------------------- | ------------------------------------------------------------ |
| Start "Service Parse" as cronjob | In crontab: `0,30 * * * * python3 /path/to/service_parse.py 2> /path/to/service_parse.log` |
| Start "Service ZIP" as cronjob   | In crontab: `15,45 * * * * python3 /path/to/service_zip.py 2> /path/to/service_zip.log` |

## Program Sturcture 

The Program consists of two small services. The first one to download, parse and upload the files and the second one to download,  zip, upload and email the processed files. The following diagram shows the whole process in detail.

![](/home/giosuel/Projects/TBZ/m122_lb02/assets/flowchart.png)

There are there parts of the software.

- Service Parser
- Service Zipper
- Common Modules

The Parsing and zipper services are visible in the above Illustration. The common modules are meant to provide a neutral interface to both services for common functionalities. The goal was to move most of the code into the common part since this code is generic and can be reused easily.

There are four parts of the common modules part.

- Network Module (Upload and Download Files from a Server)
- Config Module (Read configs form config files)
- Auto Parser Module (Auto Parser to parse files)
- Cache Module (Read and write files to/from cache)


## The Auto-Parser

The auto-parser is a small library I wrote, that provides a robust interface to parse a variety of files. It is meant to be used to parse a file, regardless of it's format or type. The auto-parser works with template files, that contain specific placeholders. Here is a brief overview how the auto-parser works.

 ![](/home/giosuel/Projects/TBZ/m122_lb02/assets/autoparser.png)

The auto-parser only processes placeholders that are in the format `$autoparse_XY` where X and Y are the coordinates for the data matrix. All other parameters have to specified in the "ignore dictionary" or "static value dictionary". If there are any other placeholders, that are not specified, the program will not process the file and throw an error.

### Example

#### Data File (Data Matrix)

```csv
value00;value01;value02
value10;value11;value12
```

#### Before Auto-Parsing

```xml
<head>
	<title>$autoparse_01</title>
    <script src="$autoparse_12"></script>
</head>
<body>
	$static_content
</body>
```

#### After Auto-Parsing

```xml
<head>
	<title>value01</title>
    <script src="value12"></script>
</head>
<body>
	"Lorem Ipsum"
</body>
```


## Logging

Each service has an own log file called like the service. Since only the console logs are colored, it is recommended to pipe `STDOUT` to the log file instead of using the built-in functions. This is set by default but can be changed in the main files of each service.

### Configuration

The program was built to be highly configurable. I will explain the following configurations and their purpose in the next table. 

#### Config JSON

```json
{
    "patterns":{
        "receipt": "quittungsfile\\d{8}_\\d{6}\\.txt",
        "invoice": "rechnung\\d+\\.data"
    },
    "formats": {
        "date_email": "%d.%m.%Y",
        "time_email": "%H:%M:%S",
        "date_file": "%Y%m%d",
        "time_file": "%H%M%S",
        "date_invoice": "%d.%m.%Y"
    },
    "cache_folder": "./data/cache",
    "email_template": "./data/templates/email.txt",
    "email_sender": "payment@mail.ch",
    "email_sender_name": "Payment System",
    "template_invoice_xml": "./data/templates/invoice.xml",
    "template_invoice_txt": "./data/templates/invoice.txt",
    "template_invoice_positions_xml": "./data/templates/invoice_position.xml",
    "template_invoice_positions_txt": "./data/templates/invoice_position.txt"
}

```

| Configuration Parameter          | Description                                              |
| -------------------------------- | -------------------------------------------------------- |
| `patterns/receipt`               | Regex for the receipt file name                          |
| `patterns/invoice`               | Regex for the invoice file name                          |
| `formats/date_email`             | The date format that is used user facing (Email and XML) |
| `formats/time_email`             | The time format that is used user facing (Email and XML) |
| `formats/date_file`              | The date format that is used in the receipt file name    |
| `formats/time_file`              | The time format that is used in the receipt file name    |
| `formats/date_invoice`           | The date format that is required for the invoice         |
| `cache_folder`                   | The cache folder                                         |
| `email_template`                 | Email template location                                  |
| `email_sender`                   | Email sender                                             |
| `email_sender_name`              | Email sender name                                        |
| `template_invoice_xml`           | Invoice XML template location                            |
| `template_invoice_txt`           | Invoice TXT template location                            |
| `template_invoice_positions_xml` | Invoice positions XML template location                  |
| `template_invoice_positions_txt` | Invoice positions TXT template location                  |

### Server Customer, Payment and Email

```json
{
    "hostname": "ftp.haraldmueller.ch",
    "username": "***************",
    "password": "***************",
    "files_out": "out/AP17bGribi",
    "files_in": "in/AP17bGribi"
}
```

```json
{
    "hostname": "134.119.225.245",
    "username": "***************",
    "password": "***************",
    "files_out": "out/AP17bGribi",
    "files_in": "in/AP17bGribi"
}
```

```json
{
    "hostname": "smtp.mail.ch",
    "username": "payment@mail.ch",
    "password": "***************"
}
```

| Configuration Parameter                | Description             |
| -------------------------------------- | ----------------------- |
| `hostname`                             | Hostname of the server  |
| `password`                             | Password to log in with |
| `username`                             | Username to log in with |
| `files_in` (Only Customer and Payment) | File in directory       |
| `files_out`(Only Customer and Payment) | Files out directory     |
