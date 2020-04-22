from os import listdir, path, makedirs, chdir, system, getcwd
from shutil import copyfile


def generateDockerFile(fns):
    dfiles = listdir("./generated")
    print(dfiles)

    for f in fns:
        fname, fext = f.split(".")
        print(fname)
        print(fext)

        if fname in dfiles:
            print("Error: Service Already Exists")
        else:
            #Create new path for Dockefile
            newpath = "./generated/" + fname
            if not path.exists(newpath):
                makedirs(newpath)

            #copy file to new location
            copyfile("./functions/" + f, "./generated/" + fname + "/" + f)

            #Generate Dockerfile
            df = open(newpath + "/Dockerfile", "a")

            df.write("FROM python:3" + '\n')
            df.write("ADD " + f + " /" + '\n')
            df.write("CMD [ 'python', './" + f + "' ]" + '\n')
            df.close()
            
            # Build and Push Image 
            initialDir = getcwd()

            chdir(newpath)

            system("docker build -t laemtl/gini_serverless_services:" + fname + " .")
            system("docker push laemtl/gini_serverless_services:" + fname)
            
            chdir(initialDir)
         
# Function was created to get imports, but in the end the dockerfile did not need them
# In practice we would add the dependencies based on a dependency file
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
                    dList = dList + " " + d
            else:
                inImports = False
                break
        except:
            inImports = False
            break
    
    return dList.strip()


# Get list of function and generate dockerfile for each
l = listdir("./functions")
generateDockerFile(l)