import boto3
import json

def get_credentials(account_id, role_name="YourRoleName"):
    """
    Assume a role and return temporary credentials.
    """
    try:
        sts = boto3.client('sts')
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        assumed_role_object = sts.assume_role(
            RoleArn=role_arn, RoleSessionName="NetworkDocumentationSession")
        return {
            'AccessKeyId': assumed_role_object['Credentials']['AccessKeyId'],
            'SecretAccessKey': assumed_role_object['Credentials']['SecretAccessKey'],
            'SessionToken': assumed_role_object['Credentials']['SessionToken']
        }
    except Exception as e:
        print(f"Error assuming role for account {account_id}: {str(e)}")
        return None


def get_account_documentation(account_id):
    """
    Get documentation for the given account ID.
    """
    account_info = {}
    try:
        credentials = get_credentials(account_id)
        if not credentials:
            return account_info

        for region in get_available_regions():
            with boto3.Session(aws_access_key_id=credentials['AccessKeyId'],
                               aws_secret_access_key=credentials['SecretAccessKey'],
                               aws_session_token=credentials['SessionToken'],
                               region_name=region) as session:
                region_info = {}
                region_info['vpcs'] = get_vpcs(session)
                region_info['subnets'] = get_subnets(session)
                region_info['security_groups'] = get_security_groups(session)
                region_info['network_acls'] = get_network_acls(session)
                region_info['route_tables'] = get_route_tables(session)
                region_info['vpc_endpoints'] = get_vpc_endpoints(session)
                region_info['vpc_peering_connections'] = get_vpc_peering_connections(
                    session)
                region_info['load_balancers'] = get_load_balancers(session)

            account_info[region] = region_info
    except Exception as e:
        print(f"Error extracting resources for account {account_id}: {str(e)}")

    return account_info

def main():
    """
    Main function to retrieve and store network documentation for all accounts.
    """
    organizations = boto3.client('organizations')
    root_id = get_root_id(organizations)
    ous = get_ous(organizations, root_id)
    accounts = get_accounts(organizations, ous)

    documentation = {}
    for account in accounts:
        documentation[account['Id']] = get_account_documentation(account['Id'])

    store_documentation(documentation)

def get_root_id(organizations):
    """
    Retrieve the root ID of the AWS organization.
    """
    roots = organizations.list_roots()
    return roots['Roots'][0]['Id']

def get_ous(organizations, root_id):
    """
    Retrieve the Organizational Units (OUs) for the given root ID.
    """
    ous = organizations.list_organizational_units_for_parent(ParentId=root_id)
    return ous['OrganizationalUnits']

def get_accounts(organizations, ous):
    """
    Retrieve the accounts associated with the given Organizational Units (OUs).
    """
    accounts = []
    for ou in ous:
        ou_accounts = organizations.list_accounts_for_parent(ParentId=ou['Id'])
        accounts.extend(ou_accounts['Accounts'])
    return accounts

def get_available_regions():
    """
    Retrieve the list of available AWS regions.
    """
    ec2 = boto3.client('ec2', region_name='us-east-1')
    regions = ec2.describe_regions()
    return [region['RegionName'] for region in regions['Regions']]

def get_vpcs(session):
    """
    Retrieve a list of VPCs for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        vpcs = ec2.describe_vpcs()
        return vpcs['Vpcs']
    except Exception as e:
        print(
            f"Error retrieving VPCs for region {session.region_name}: {str(e)}")
        return []

def get_subnets(session):
    """
    Retrieve a list of subnets for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        subnets = ec2.describe_subnets()
        return subnets['Subnets']
    except Exception as e:
        print(
            f"Error retrieving subnets for region {session.region_name}: {str(e)}")
        return []

def get_security_groups(session):
    """
    Retrieve a list of security groups for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        security_groups = ec2.describe_security_groups()
        return security_groups['SecurityGroups']
    except Exception as e:
        print(
            f"Error retrieving security groups for region {session.region_name}: {str(e)}")
        return []

def get_network_acls(session):
    """
    Retrieve a list of network ACLs for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        network_acls = ec2.describe_network_acls()
        return network_acls['NetworkAcls']
    except Exception as e:
        print(
            f"Error retrieving network ACLs for region {session.region_name}: {str(e)}")
        return []

def get_route_tables(session):
    """
    Retrieve a list of route tables for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        route_tables = ec2.describe_route_tables()
        return route_tables['RouteTables']
    except Exception as e:
        print(
            f"Error retrieving route tables for region {session.region_name}: {str(e)}")
        return []

def get_vpc_endpoints(session):
    """
    Retrieve a list of VPC endpoints for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        vpc_endpoints = ec2.describe_vpc_endpoints()
        return vpc_endpoints['VpcEndpoints']
    except Exception as e:
        print(
            f"Error retrieving VPC endpoints for region {session.region_name}: {str(e)}")
        return []

def get_vpc_peering_connections(session):
    """
    Retrieve a list of VPC peering connections for the given AWS session.
    """
    try:
        ec2 = session.client('ec2')
        vpc_peering_connections = ec2.describe_vpc_peering_connections()
        return vpc_peering_connections['VpcPeeringConnections']
    except Exception as e:
        print(
            f"Error retrieving VPC peering connections for region {session.region_name}: {str(e)}")
        return []

def get_load_balancers(session):
    """
    Retrieve a list of load balancers for the given AWS session.
    """
    try:
        elbv2 = session.client('elbv2')
        load_balancers = elbv2.describe_load_balancers()
        return load_balancers['LoadBalancers']
    except Exception as e:
        print(
            f"Error retrieving load balancers for region {session.region_name}: {str(e)}")
        return []

def store_documentation(documentation):
    """
    Store the collected network documentation in an S3 bucket.
    """
    s3 = boto3.client('s3')
    s3.put_object(Bucket='your-documentation-bucket',
                  Key='network-documentation.json', Body=json.dumps(documentation))

if __name__ == '__main__':
    main()
