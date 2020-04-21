from os import listdir, path, makedirs

def generateDockerFile(fns):
    dfiles = listdir("./generated")
    print(dfiles)

    for f in fns:
        fname, fext = f.split(".")
        print(fname)
        print(fext)

        if fname in dfiles:
            print("Docker File Already Generated")
        else:
            #Get list of dependencies 
            dependencyList = getDependencies(f)

            #Create new path for Dockefile
            newpath = "./generated/" + fname
            if not path.exists(newpath):
                makedirs(newpath)

            #Generate Dockerfile
            df = open(newpath + "/Dockerfile", "a")
            df.write("FROM python:3" + '\n')
            df.write("ADD " + f + " /" + '\n')
            df.write("RUN pip install " + dependencyList + '\n')
            df.write("CMD [ 'python', './" + f + "' ]" + '\n')

            df.close()

# THIS FUNCTION IS RLY SKETCHY
def getDependencies(f):
    dList = ""
    file = open("./functions/" + f, 'r')
    inImports = True

    while inImports:
        try:
            l = file.readline()
            print(l)

            keyword, rest = l.split(" ", 1)

            if keyword == "from":
                d = rest.split()[0]
                dList = dList + " " + d + " "
            elif keyword == "import":
                rest = rest.replace('\n','')
                rest = rest.replace(' ','')
                deps = rest.split(",")

                for d in deps:
                    dList = dList + " " + d + " "
            else:
                inImports = False
                break
        except:
            inImports = False
            break
    
    return dList.strip()


        
 
l = listdir("./functions")
generateDockerFile(l)

#print(getDependencies("WeatherFunction_v1.py"))
