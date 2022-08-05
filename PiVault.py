'''
Very simply secrets vault. 
 - Takes in a string, encrypts it and stores the encrypted string.
 - Then retrieves the encrypted string and decrypts it for use

Author Siggi Bjarnason AUG 2022
Copyright 2022

Encrypt/decrypt functions copied from https://stackoverflow.com/a/44212550/8549454

Following packages need to be installed
pip install pycryptodome
pip install maskpass
pip install pyperclip

'''
# Import libraries
import os
import time
import sys
import subprocess
import base64
from xml.dom.expatbuilder import InternalSubsetExtractor

try:
  from Crypto.Cipher import AES
  from Crypto.Hash import SHA256
  from Crypto import Random
except ImportError:
  subprocess.check_call(
      [sys.executable, "-m", "pip", "install", 'pycryptodome'])
finally:
  from Crypto.Cipher import AES
  from Crypto.Hash import SHA256
  from Crypto import Random
try:
  import maskpass
except ImportError:
  subprocess.check_call(
      [sys.executable, "-m", "pip", "install", 'maskpass'])
finally:
  import maskpass
try:
  import pyperclip
except ImportError:
  subprocess.check_call(
      [sys.executable, "-m", "pip", "install", 'pyperclip'])
finally:
  import pyperclip

# End imports

# Global constants
bDefHide = False
strDefValueColor = "red"
strDefVault = "VaultData"
strCheckValue = "This is a simple secrets vault"
strCheckFile = "VaultInit"
bLoggedIn = False

#functions 

def StringEncryptor(strkey, strData, encode=True):
  """
  This handles encrypting a string using AES.
  Adopted from https://stackoverflow.com/a/44212550/8549454
  Parameters:
    strkey: Simple string with encryption password
    strData: Simple string with the data to be encrypted
    encode: Optional, defaults to true. A boolean to indicate the return should be Base64 encoded.
  Returns:
    Encrypted string, either raw or base64 encoded depending on the encode parameter
  """
  bKey = bytes(strkey, "UTF-8")
  bData = bytes(strData, "UTF-8")  # use SHA-256 over our key to get a proper-sized AES key
  hKey = SHA256.new(bKey).digest()
  IV = Random.new().read(AES.block_size)  # generate IV
  objEncryptor = AES.new(hKey, AES.MODE_CBC, IV)  # calculate needed padding
  iPadLen = AES.block_size - len(bData) % AES.block_size
  bData += bytes([iPadLen]) * iPadLen  # store the IV at the beginning and encrypt
  oEncrypted = IV + objEncryptor.encrypt(bData)
  return base64.b64encode(oEncrypted).decode("UTF-8") if encode else oEncrypted

def StringDecryptor(strkey, strData, decode=True):
  """
  This handles decrypting a string encrypted with AES
  Adopted from https://stackoverflow.com/a/44212550/8549454
  Parameters:
    strkey: Simple string with encryption password
    strData: Simple string with the encrypted data
    encode: Optional, defaults to true. A boolean to indicate if the data is Base64 encoded.
  Returns:
    Decrypted clear text simple string
  """
  if decode:
      strData = base64.b64decode(strData.encode("UTF-8"))
  bKey = bytes(strkey, "UTF-8")
  hKey = SHA256.new(bKey).digest()
  IV = strData[:AES.block_size]  # extract the IV from the beginning
  objEncryptor = AES.new(hKey, AES.MODE_CBC, IV)
  bClear = objEncryptor.decrypt(strData[AES.block_size:])  # decrypt
  iPadLen = bClear[-1]  # pick the padding value from the end;
  if bClear[-iPadLen:] != bytes([iPadLen]) * iPadLen:
      raise ValueError("Invalid padding...")
  bClear = bClear[:-iPadLen]  # remove the padding
  return bClear.decode("UTF-8")

def GetFileHandle(strFileName, strperm):
  """
  This wraps error handling around standard file open function 
  Parameters:
    strFileName: Simple string with filename to be opened
    strperm: single character string, usually w or r to indicate read vs write. other options such as "a" are valid too.
  Returns:
    File Handle object
  """
  dictModes = {}
  dictModes["w"] = "writing"
  dictModes["r"] = "reading"
  dictModes["a"] = "appending"
  dictModes["x"] = "opening"

  cMode = strperm[0].lower()

  try:
    objFileOut = open(strFileName, strperm, encoding='utf8')
    return objFileOut
  except PermissionError:
    print("unable to open output file {} for {}, "
              "permission denied.".format(strFileName, dictModes[cMode]))
    return("Permission denied")
  except FileNotFoundError:
    print("unable to open output file {} for {}, "
              "Issue with the path".format(strFileName, dictModes[cMode]))
    return("key not found")

def DefineMenu():
  """
  Simple function that loads the menu into a global dictionary dictMenu
  Parameters:
    none
  Returns:
    Sets global variable dictMenu but returns nothing
  """
  global dictMenu

  dictMenu = {}
  dictMenu["help"]  = "Displays this message. Can also use /h -h and --help"
  dictMenu["quit"]  = "exit out of the script"
  dictMenu["add"]   = "Adds a new key value pair"
  dictMenu["list"]  = "List out all keys"
  dictMenu["fetch"] = "fetch a specified key"
  dictMenu["clippy"] = "put specified key value on the clipboard"
  dictMenu["passwd"] = "Change the password"

def DefineColors():
  """
  Simple function that loads the dictColor dictionary of colors
  Parameters:
    none
  Returns:
    Sets global variable dictColor but returns nothing
  """
  global dictColor
  dictColor = {}
  dictColor["black"] = "30"
  dictColor["red"] = "31"
  dictColor["green"] = "32"
  dictColor["orange"] = "33"
  dictColor["blue"] = "34"
  dictColor["purple"] = "35"
  dictColor["cyan"] = "36"
  dictColor["lightgrey"] = "37"
  dictColor["darkgrey"] = "90"
  dictColor["lightred"] = "91"
  dictColor["lightgreen"] = "92"
  dictColor["yellow"] = "93"
  dictColor["lightblue"] = "94"
  dictColor["pink"] = "95"
  dictColor["lightcyan"] = "96"

def UserLogin():
  """
  Simple function that handles validating that password is valid across all items in the vault
  Parameters:
    none
  Returns:
    true/false boolean to indicate if password supplied is good or not
  """
  global strPWD
  global bLoggedIn

  if strPWD == "":
    strPWD = maskpass.askpass(prompt="Please provide vault password: ", mask="*")
  bStatus = CheckVault()
  if bStatus is None:
    if len(lstVault) > 0:
      if FetchItem(lstVault[0]) == "Failed to decrypt":
        print("unable to decrypt vault, please try to login again")
        return False
    AddItem(strCheckFile, strCheckValue)
    print("Vault Initialized")
    bStatus = True
    return True
  elif bStatus:
    print("Password is good")
    bStatus = True
    return True
  else:
    print("unable to decrypt vault, please try again")
    return False

def AddItem(strKey,strValue,bConf=True,strPass=""):
  """
  Function that encrypts the string provided and 
  stores the key value pair in the choosen data store
  Parameters:
    strKey: The name of the key part of the key value pair
    strValue: The value part of the key value pair
    bConf: Optional, defaults to True. If key updates should be confirmed
    strPass: Optional, defaults to blank string. Use a password other than 
              that validated by login function
  Returns:
    True/false boolean to indicate if the was successful or not
  """
  if strPass == "":
    strPass = strPWD
  strFileOut = strVault + strKey
  if os.path.exists(strFileOut) and bConf:
    print("Key '{}' already exists, do you wish to overwrite it?".format(strKey))
    strResp = input("Please type yes to confirm, all other input is a no: ")
    if strResp.lower() != "yes":
      return False

  tmpResponse = GetFileHandle(strFileOut, "w")
  if isinstance(tmpResponse, str):
    print(tmpResponse)
    return False
  else:
    objFileOut = tmpResponse
    objFileOut.write(StringEncryptor(strPass, strValue))
    objFileOut.close()
    return True

def FetchItem(strKey):
  """
  Function that fetches the specified key from the datastore and decrypts it.
  Parameters:
    strKey: The name of the key to be fetched
  Returns:
    Either the decrypted string or boolean false to indicate a failure
  """
  strFileIn = strVault + strKey
  tmpResponse = GetFileHandle(strFileIn, "r")
  if isinstance(tmpResponse, str):
    print(tmpResponse)
    return False
  else:
    objFileIn = tmpResponse
    strValue = objFileIn.read()
    objFileIn.close()
    try:
      return StringDecryptor(strPWD, strValue)
    except ValueError:
      print("Failed to decrypt the vault")
      return False

def Fetch2Clip(strKey):
  """
  Function that fetches the specified key from the datastore and decrypts it.
  Decrypted value is then placed on the clipboard and not shown.
  Parameters:
    strKey: The name of the key to be fetched
  Returns:
    nothing
  """
  strValue = FetchItem(strKey)
  if strValue != False:
    try:
      pyperclip.copy(strValue)
      print("Value for {} put on the clipboard".format(strKey))
    except pyperclip.PyperclipException:
      print("Failed to find the clipboard, so outputting it here")

def ListItems():
  """
  Function that just lists out all the keys in the store.
  Parameters:
    none
  Returns:
    nothing
  """
  if len(lstVault) > 0:
    print("\nHere are all the keys in the vault:")
    for strItem in lstVault:
      if strItem != strCheckFile:
        print("{}".format(strItem))

def CheckVault():
  """
  Function used by login function to check the vault.
  Parameters:
    none
  Returns:
    true/false indicating if the vault is good or not
  """
  if strCheckFile in lstVault:
    strInitstr = FetchItem(strCheckFile)
    if strInitstr == strCheckValue:
      return True
    else:
      return False
  else:
    return None

def DisplayHelp():
  """
  Function that displays a help message.
  Parameters:
    none
  Returns:
    none
  """
  print("\nHere are the commands you can use:")
  for strItem in dictMenu:
    if len(lstVault) > 1:
      if strItem != "clippy" or bClippy:
        print("{} : {}".format(strItem, dictMenu[strItem]))
    elif strItem != "list" and strItem != "fetch" and strItem != "clippy":
      print("{} : {}".format(strItem, dictMenu[strItem]))

def ChangePWD():
  """
  Function that loops through all items in the store, decrypts it then re-encrypts with new password.
  Parameters:
    none
  Returns:
    nothing
  """
  strNewPWD = maskpass.askpass(prompt="Please provide New password: ", mask="*")
  for strKey in lstVault:
    strValue = FetchItem(strKey)
    if AddItem(strKey, strValue,False,strNewPWD):
      print("key {} successfully changed".format(strKey))
    else:
      print("Failed to change key {}".format(strKey))

def ProcessCMD(objCmd):
  """
  Function that process all the user commands, whether in the shell or from command arguments.
  Parameters:
    objCmd: The command string, either simple string or an array of strings
  Returns:
    nothing
  """
  global bCont

  strCmd = ""
  lstCmd = []
  if isinstance(objCmd,str):
    lstCmd = objCmd.split()
  elif isinstance(objCmd,list):
    lstCmd = objCmd
  else:
    print("Can't deal with command of type {}".format(type(objCmd)))
    return
  if len(lstCmd) > 0:
    strCmd = lstCmd[0]
  else:
    print("Got an empty list, don't know what to do with that")
    return

  strCmd = strCmd.replace("-", "")
  strCmd = strCmd.replace("/", "")
  strCmd = strCmd.replace("\\", "")
  strCmd = strCmd.replace("<", "")
  strCmd = strCmd.replace(">", "")
  strCmd = strCmd.lower()
  if strCmd == "q" or strCmd == "quit" or strCmd == "exit":
    bCont = False
    print("Goodbye!!!")
    return
  if strCmd == "h":
    strCmd = "help"
  if strCmd not in dictMenu:
    print("command {} not valid".format(strCmd))
    return
  if strCmd == "help":
    DisplayHelp()
  elif strCmd == "add":
    bLogin = True
    if not bLoggedIn:
      bLogin = UserLogin()
    if bLogin:
      if len(lstCmd) > 1:
        strKeyName = lstCmd[1]
      else:
        strKeyName = input("Please specify keyname: ")
      if len(lstCmd) > 2:
        strKeyValue = " ".join(lstCmd[2:])
      else:
        if bHideValueIn:
          strKeyValue = maskpass.askpass(
              prompt="Please specify the value for key {}: ".format(strKeyName), mask="*")
        else:
          strKeyValue = input("Please specify the value for key {}: ".format(strKeyName))
      if AddItem(strKeyName,strKeyValue):
        print("key {} successfully created".format(strKeyName))
        ListCount()
      else:
        print("Failed to create key {}".format(strKeyName))
  elif strCmd == "list":
    ListItems()
  elif strCmd == "passwd":
    ChangePWD()
  elif strCmd == "fetch":
    bLogin = True
    if not bLoggedIn:
      bLogin = UserLogin()
    if bLogin:
      if len(lstCmd) > 1:
        strKey = lstCmd[1]
      else:
        ListItems()
        strKey = input("Please provide name of key you wish to fetch: ")
      strValue = FetchItem(strKey)
      if strValue != False:
        print("\nThe value of '{}' is:{} {}{}\n".format(
            strKey, strFormat, strValue, strFormatReset))
  elif strCmd == "clippy":
    if not bClippy:
      print("Clippy is not supported on your system")
      return
    bLogin = True
    if not bLoggedIn:
      bLogin = UserLogin()
    if bLogin:
      if len(lstCmd) > 1:
        strKey = lstCmd[1]
      else:
        ListItems()
        strKey = input("Please provide name of key you wish to fetch: ")
      Fetch2Clip(strKey)
  else:
    print("Not implemented")

def ListCount():
  """
  Function that displays information about status of the vault and number of members.
  Parameters:
    none
  Returns:
    nothing
  """

  global lstVault
  
  lstVault = os.listdir(strVault)
  if strCheckFile in lstVault:
    iVaultLen = len(lstVault) - 1
  else:
    iVaultLen = len(lstVault)
  if iVaultLen > 0:
    print("Vault is initialized and contains {} entries".format(iVaultLen))
  else:
    print("Vault is uninilized, need to add an item to initialize")

def FetchEnv(strVarName):
  """
  Function that fetches the specified content of specified environment variable, 
  converting nonetype to empty string.
  Parameters:
    strVarName: The name of the environment variable to be fetched
  Returns:
    The content of the environment or empty string
  """

  if os.getenv(strVarName) != "" and os.getenv(strVarName) is not None:
    return os.getenv(strVarName)
  else:
    return ""

def main():
  global bCont
  global strVault
  global strPWD
  global bClippy
  global bHideValueIn
  global strFormat
  global strFormatReset
  
  DefineMenu()
  DefineColors()

  lstSysArg = sys.argv

  strBaseDir = os.path.dirname(sys.argv[0])
  strRealPath = os.path.realpath(sys.argv[0])
  strRealPath = strRealPath.replace("\\", "/")
  if strBaseDir == "":
    iLoc = strRealPath.rfind("/")
    strBaseDir = strRealPath[:iLoc]
  if strBaseDir[-1:] != "/":
    strBaseDir += "/"
  strVersion = "{0}.{1}.{2}".format(
      sys.version_info[0], sys.version_info[1], sys.version_info[2])

  print("This is a simple secrets vault script. Enter in a key value pair "
        "and the value will be encrypted with AES and stored under the key.")
  print ("This is running under Python Version {}".format(strVersion))
  print("Running from: {}".format(strRealPath))
  dtNow = time.asctime()
  print("The time now is {}".format(dtNow))

  try:
    pyperclip.paste()
    print("Clipboard seems good so turning that on")
    bClippy = True
  except pyperclip.PyperclipException:
    print("Failed to find the clipboard, so turning clippy off")
    bClippy = False

  strVault = FetchEnv("VAULT")
  strPWD = FetchEnv("PWD")
  strHideIn = FetchEnv("HIDEINPUT")
  strValueColor = FetchEnv("VALUECOLOR")
  if strVault != "":
    print("Found {} in env for vault path".format(strVault))
  else:
    print("no vault environment valuable")
  if strHideIn == "":
    bHideValueIn = bDefHide
  elif strHideIn.lower() == "true":
    bHideValueIn = True
  else:
    bHideValueIn = False
  if strValueColor == "":
    iColorID = dictColor[strDefValueColor]
  else:
    iColorID = dictColor[strValueColor]

  strFormat = "\x1b[1;{}m".format(iColorID)
  strFormatReset = "\x1b[0;0m"
  if len(lstSysArg) > 1:
    if lstSysArg[1][:5].lower() == "vault":
      strVault = lstSysArg[1][6:]
      print("Found vault in argument: {}".format(strVault))
      del lstSysArg[1]
    
  if strVault == "":
    strVault = strBaseDir + strDefVault + "/"
    print("No vault path provided in either env or argument. Defaulting vault path to: {}".format(strVault))
  else:
    print("Using vault path of {}".format(strVault))

  strVault = strVault.replace("\\", "/")
  if strVault[-1:] != "/":
    strVault += "/"

  if not os.path.exists(strVault):
    os.makedirs(strVault)
    print("\nPath '{0}' for vault didn't exists, so I create it!\n".format(strVault))
  

  if len(lstSysArg) > 1:
    ListCount()
    bCont = False
    del lstSysArg[0]
    ProcessCMD(lstSysArg)
  else:
    bCont = True
  
  while bCont:
    ListCount()
    DisplayHelp()
    strCmd = input("Please enter a command: ")
    ProcessCMD(strCmd)




if __name__ == '__main__':
    main()
