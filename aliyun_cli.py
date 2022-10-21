import warnings
warnings.filterwarnings("ignore")
from PyInquirer import prompt
from examples import custom_style_2
from prompt_toolkit.validation import Validator, ValidationError
import sys
from pprint import pprint
import base64
from typing import List
import pandas as pd
import prettytable as pt
import time
from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass
    @staticmethod
    def create_client(
            access_key_id: str,
            access_key_secret: str,
    ) -> Ecs20140526Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的 AccessKey ID,
            access_key_id=access_key_id,
            # 您的 AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = f'ecs-cn-hangzhou.aliyuncs.com'
        return Ecs20140526Client(config)

    @staticmethod
    def get_all_regions(
        args: List[str],
    ) -> None:
        client = Sample.create_client(args[0], args[1])
        describe_regions_request = ecs_20140526_models.DescribeRegionsRequest()
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            return client.describe_regions_with_options(describe_regions_request, runtime)
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def get_all_ecs(
            args: List[str],
    ) -> None:
        client = Sample.create_client(args[0], args[1])
        datas = []
        startpage = 1
        runtime = util_models.RuntimeOptions()
        size = 50
        while 1 :
            describe_instances_request = ecs_20140526_models.DescribeInstancesRequest(
                page_number=startpage,
                page_size=size,
                region_id=args[2]
            )
            try:
                # 复制代码运行请自行打印 API 的返回值
                data =  client.describe_instances_with_options(describe_instances_request, runtime)
                if data:
                    # print('pc num',len(data.body.to_map()['Instances']['Instance']))
                    # print('TotalCount', data.body.to_map()['TotalCount'])
                    if ( len(data.body.to_map()['Instances']['Instance'])<=size and data.body.to_map()['TotalCount'] <= size):
                        for i in data.body.to_map()['Instances']['Instance']:
                            datas.append(i)
                        return datas
                    elif len(data.body.to_map()['Instances']['Instance'])< size and data.body.to_map()['TotalCount'] >= size :
                        for i in data.body.to_map()['Instances']['Instance']:
                            datas.append(i)
                        return datas
                    else:
                        for i in data.body.to_map()['Instances']['Instance']:
                            datas.append(i)
                        startpage+=1
                else:
                    return datas
            except Exception as error:
                UtilClient.assert_as_string(error.message)
                return datas
        return datas

    @staticmethod
    def cmd(ak,info,command,times = 12):
        client = Sample.create_client(ak[0], ak[1])
        optype = 'RunShellScript'
        if info['OSType'] == 'windows':
            optype = 'RunPowerShellScript'

        run_command_request = ecs_20140526_models.RunCommandRequest(
            region_id=info['RegionId'],
            instance_id= [info['InstanceId']],
            type=optype,
            command_content=command
        )
        
        runtime = util_models.RuntimeOptions()
        command_id = client.run_command_with_options(run_command_request, runtime).body.to_map()['CommandId']
        for i in range(times) :
            try:
                describe_invocation_results_request = ecs_20140526_models.DescribeInvocationResultsRequest(
                    region_id=info['RegionId'],
                    instance_id=info['InstanceId'],
                    command_id = command_id
                )
                rep =  client.describe_invocation_results_with_options(describe_invocation_results_request, runtime)
                data = [ i['Output'] for i in rep.to_map()['body']['Invocation']['InvocationResults']['InvocationResult']]
                if data[0]:
                    return decode(data)
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
                
            

def get_all_ecs(ak):
    regions = Sample.get_all_regions(ak).body.to_map()['Regions']['Region']
    ecss = []
    for i in regions:
        args = [ak[0],ak[1],i['RegionId']]
        ecs = Sample.get_all_ecs(args)
        if ecs :
            print(i['RegionId'],'find:',len(ecs))
            ecss+=ecs
    return ecss



def print_table(data):    
    for i in data:
        if i['PublicIpAddress']['IpAddress']:
            i.update({'PublicIp': i['PublicIpAddress']['IpAddress'][0]})
        else:
            i.update({'PublicIp': 'null'})

    df = pd.DataFrame.from_dict(data)
    df.rename(columns={'InternetMaxBandwidthOut': '宽带','InstanceId':'实例id','RegionId':'区域','Memory':'内存','HostName':'主机名','InstanceName':'实例名','OSType':'系统','Description':'描述','Status':'状态','PublicIp':'公网ip'},inplace=True)
    
    
    newDf = pd.DataFrame(df, columns=['编号','区域', '实例id','系统','Cpu', '内存', '宽带','主机名', '实例名', '描述','状态', '公网ip', 'OSName',])
    tb = pt.PrettyTable()
    
#     tb = ColorTable(theme=Themes.OCEAN)
    for col in newDf.columns.values:
        tb.add_column(col, df[col])
    print(tb)
    
     
def query_region(data,InstanceId):
    
    info = {}
    for i in data:
        if i['编号'] == int(InstanceId):
            info ['RegionId']= i['RegionId']
            info ['InstanceId']= i['InstanceId']
            info ['OSType'] = i['OSType']
    return info

def decode(data):
    return '\n'.join([base64.b64decode(i).decode() for i in data ])

    
secretkey  ={'type': "input","name": "secret",     "message": "输入secretkey",}
accessid={'type': "input","name": "id",     "message": "(q 退出)输入accesskey id",}
cmd   = {'type': "input","name": "cmd",    "message": "(q 返回上级)  shell:"}
server = {'type': "input","name": "server_id","message": "(q 返回上级) 输入编号: ",}



def main():
    while 1 :
        keyid = prompt(accessid, style=custom_style_2).get("id")
        if keyid == 'q':
            break
        elif keyid == '':
            pass
        secret = prompt(secretkey, style=custom_style_2).get("secret")

        ak = [keyid, secret]
        try:
            data = get_all_ecs(ak)
            if data:
                name = f'ecs_{keyid}_'+str(int(time.time()))
                df = pd.DataFrame.from_dict(data)
                df.to_csv(name+'.csv')
            for i,j in zip(data,range(1,len(data)+1)):
                i.update({'编号':j})
            print_table(data)
        except Exception as e:
            print(e)
            print('有误或者 未发现主机')
            break
        while 1:
        
            try:
                InstanceId = prompt(server, style=custom_style_2).get("server_id")
                if InstanceId == 'q':
                    break
                elif InstanceId == '':
                    pass
                else:
                    info = query_region(data, InstanceId)
                    print('已选择实例：',' | '.join([i for i in info.values()]))
                    while 1:
                        command = prompt([cmd], style=custom_style_2).get("cmd")
                        if command == 'q':
                            break
                        elif command == '':
                            pass
                        else:
                            with open(f'logs_{keyid}.txt','a')as file:
                                file.write(command+'\n')
                            rep = Sample.cmd(ak, info, command)
                            print(rep)
                            with open(f'logs_{keyid}.txt','a')as file:
                                file.write(rep)
            
            except:
                print('异常')
                print_table(data)
               


if __name__ == "__main__":
    main()

