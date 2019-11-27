# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from google.oauth2 import service_account
from google.cloud import pubsub_v1
import googleapiclient.discovery
from slugify import slugify
import os

# Get admin account credentials
credentials = service_account.Credentials.from_service_account_file(filename=os.environ['GOOGLE_APPLICATION_CREDENTIALS'], scopes=['https://www.googleapis.com/auth/cloud-platform'])
# Create the Cloud IAM service object (to manage service accounts)
googleIAM = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)
# Create the Pub/Sub subscriber object
subscriber = pubsub_v1.SubscriberClient()
# Create the Pub/Sub publisher object
publisher = pubsub_v1.PublisherClient()

class B2bClients(models.Model):
    _name = 'b2b.client'
    _description = "B2B Client"
    _rec_name = 'partner'

    """
    ╔═╗╔═╗╔═╗╔═╗╦  ╔═╗  ╔═╗╦  ╔═╗╦ ╦╔╦╗
    ║ ╦║ ║║ ║║ ╦║  ║╣   ║  ║  ║ ║║ ║ ║║
    ╚═╝╚═╝╚═╝╚═╝╩═╝╚═╝  ╚═╝╩═╝╚═╝╚═╝═╩╝
    HELPER METHODS
    Defined here to keep logic simple

    """

    @staticmethod
    def __remove_policy_members(policy, role, members):
        for member in members:
            for binding in policy.bindings:
                if binding.role == role:
                    # Remove one member
                    if member in binding.members:
                        binding.members.remove(member)
                    # If not have more members remove binding obj
                    # Keep the house clean my friend!
                    if not binding.members:
                        policy.bindings.remove(binding)
                    break
        return policy

    # SERVICE ACCOUNTS ----------------------------------------------------------------------

    @api.model
    def __create_service_account(self):
        if self.partner:
            result = googleIAM.projects().serviceAccounts().create(
                name='projects/' + os.environ['GOOGLE_CLOUD_PROJECT_ID'],
                body={
                    'accountId': slugify(self.partner.name),
                    'serviceAccount': {
                        'displayName': self.partner.ref,
                        'description': 'Cuenta de Usuario'
                    }
                }
            ).execute()

            return result.get('email', False)
        return False

    @api.model
    def __create_service_account_key(self):
        if self.iam_sa and not self.iam_key:
            account_name = 'projects/-/serviceAccounts/' + self.iam_sa
            result = googleIAM.projects().serviceAccounts().keys().create(name=account_name).execute()
            return result.get('privateKeyData', False)
        return False

    @api.model
    def __delete_service_account(self):
        if self.iam_sa:
            account_name = 'projects/-/serviceAccounts/' + self.iam_sa
            return googleIAM.projects().serviceAccounts().delete(name='projects/-/serviceAccounts/' + self.iam_sa).execute()
        return False

    @api.model
    def __toggle_service_account(self):
        if self.iam_sa:
            account_name = 'projects/-/serviceAccounts/' + self.iam_sa
            # Service accounts class reference
            service = googleIAM.projects().serviceAccounts()
            # Change account status
            service.enable(name=account_name).execute() if self.active else service.disable(name=account_name).execute()
        return self.active

    # TOPICS ----------------------------------------------------------------------

    @api.model
    def __topic_path(self, item_name):
        return publisher.topic_path(os.environ['GOOGLE_CLOUD_PROJECT_ID'], item_name)

    @api.model
    def __create_topic(self, topic_path):
        topic_path = self.__topic_path(self.partner.ref)
        if publisher.create_topic(
            topic_path,
            labels={ 'partner_id': str(self.partner.id) }
        ):
            # Set topic policy
            return self.__set_topic_policy(topic_path)
        return False

    @api.model
    def __set_topic_policy(self, topic_path, role='roles/pubsub.publisher'):
        user = 'serviceAccount:' + self.iam_sa
        policy = publisher.get_iam_policy(topic_path)
        policy.bindings.add(role=role, members=[user])
        publisher.set_iam_policy(topic_path, policy)
        return policy

    @api.model
    def __delete_topic_policy(self, topic_path, role='roles/pubsub.publisher'):
        user = 'serviceAccount:' + self.iam_sa
        policy = publisher.get_iam_policy(topic_path)
        policy = self.__remove_policy_members(policy, role, [user])
        publisher.set_iam_policy(topic_path, policy)
        return policy

    @api.model
    def __delete_topic(self, topic_path):
        return publisher.delete_topic(topic_path)

    # SUBSCRIPTIONS ----------------------------------------------------------------------

    @api.model
    def __subscription_path(self, item_name):
        return subscriber.subscription_path(os.environ['GOOGLE_CLOUD_PROJECT_ID'], item_name)

    @api.model
    def __create_subscription(self, sub_path, topic_path):
        if self.partner and self.iam_sa:
            if subscriber.create_subscription(
                sub_path,
                topic_path,
                ack_deadline_seconds=10, 
                retain_acked_messages=False,
                
                expiration_policy=pubsub_v1.types.ExpirationPolicy(), # Never expire! maintained by the module
                labels={ 'partner_id': str(self.partner.id) } # Label to filter subscriptions by Odoo client id
            ):
                return self.__set_subscription_policy(sub_path)
        return False

    @api.model
    def __set_subscription_policy(self, sub_path, role='roles/pubsub.subscriber'):
        user = 'serviceAccount:' + self.iam_sa
        policy = subscriber.get_iam_policy(sub_path)
        policy.bindings.add(role=role, members=[user])
        subscriber.set_iam_policy(sub_path, policy)
        return policy

    @api.model
    def __delete_subscription_policy(self, sub_path, role='roles/pubsub.subscriber'):
        user = 'serviceAccount:' + self.iam_sa
        policy = subscriber.get_iam_policy(sub_path)
        policy = self.__remove_policy_members(policy, role, [user])
        subscriber.set_iam_policy(sub_path, policy)
        return policy

    @api.model
    def __delete_subscription(self, sub_path):
        if self.partner and self.iam_sa:
            try:
                return subscriber.delete_subscription(sub_path)
            except:
                # Return true if not exist!
                # Can be expired and deleted previously
                return True
        return False

    """
    ╔═╗╔═╗╔═╗╔═╗╦  ╔═╗  ╔═╗╔╗╔╔╦╗╔═╗ ┬
    ║ ╦║ ║║ ║║ ╦║  ║╣   ║╣ ║║║ ║║╚═╗ │
    ╚═╝╚═╝╚═╝╚═╝╩═╝╚═╝  ╚═╝╝╚╝═╩╝╚═╝ o

    """

    partner = fields.Many2one('res.partner', 'Odoo Client', ondelete='cascade', required=True, help="Select a client")
    iam_sa = fields.Char('Service Account', required =False, translate=False, help="Google IAM service account")
    iam_key = fields.Binary('Service Account Key', attachment=True, help="Google IAM service account key")
    vip = fields.Boolean('VIP Client', default=False, help="Receive all clients data, not only yours")
    send = fields.Boolean('Can Send', default=False, inverse='client_set_send_auth', help="Check to authorize this user for send data items")
    active = fields.Boolean('Active', default=True, inverse='iam_toggle_active', help="Enable or disable this client")
    products_filter = fields.Many2many('product.tag', 'product_tag_b2b_client_rel', string='Filter Products')
    items = fields.Many2many('b2b.item', 'b2b_client_item_rel', string='Data Items')

    @api.multi
    def toggle_vip(self):
        for client in self:
            # Current inverse value
            client.vip = not client.vip

    @api.multi
    def toggle_send(self):
        for client in self:
            # Current inverse value
            client.send = not client.send

    @api.multi
    def client_set_send_auth(self):
        # Change topic Policy on send change
        for client in self:
            if client.send:
                # Add roles/pubsub.publisher for current client
                client.__set_topic_policy(self.__topic_path('PUBLIC-IN'))
            else:
                # Remove roles/pubsub.publisher for current client
                client.__delete_topic_policy(self.__topic_path('PUBLIC-IN'))

    @api.multi
    def iam_toggle_active(self):
        # Change Service Account status on active change
        for client in self:
            # Enable/disable client Service Account
            client.__toggle_service_account()

    @api.model
    def create(self, vals):
        client = super(B2bClients, self).create(vals)
        # Generate service account after create
        client.iam_sa = client.__create_service_account()
        client.iam_key = client.__create_service_account_key()
        # Create customer exclusive topic
        client.__create_topic(self.__topic_path(client.partner.ref))
        # Create public topic subscription
        client.__create_subscription(self.__subscription_path('PUBLIC-OUT-' + client.partner.ref), self.__topic_path('PUBLIC-OUT'))
        # Create customer exclusive topic subscription
        client.__create_subscription(self.__subscription_path(client.partner.ref), client.partner.ref)
        return client

    @api.multi
    def unlink(self):
        # Delete Google data before unlink
        for client in self:
            # Delete public topic subscription
            client.__delete_subscription(self.__subscription_path('PUBLIC-OUT-' + client.partner.ref))
            # Delete customer exclusive topic subscription
            client.__delete_subscription(self.__subscription_path(client.partner.ref))
            # Delete customer exclusive topic
            client.__delete_topic(self.__topic_path(client.partner.ref))
            # Delete service account
            client.__delete_service_account()
            client.iam_key = False
            client.iam_sa = False
        super(B2bClients, self).unlink()
        return True