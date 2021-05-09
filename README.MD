# IoTLite

The Lite Solution for AWS IoT Core driven lights.

LEDライトの操作(IoT)用サーバーレスREST APIです。

## 課題のまとめ
ある顧客がLEDライトをスマホから遠隔制御できるアプリを開発します。アプリまたはデバイス側の開発は別のベンダーで対応します。こちらで、バックエンド開発を提供します。

### 顧客要件
- スマホアプリとLEDライト（デバイス）の間、コマンド受けるシステムを開発
  - スマホでコマンド送信 -> 作るバックエンドが受けてデバイスに送信 -> デバイスが受けて、点灯・消灯

- 対応するコマンド
  - ライトの点灯・消灯

- その他
  - SwitchでOFFになる可能性があるので、スマホアプリからLEDライトの接続性を確認するための機能
    - リアルタイム性は要求されず、数分程度の遅延で良い
  - スマホ・ライト側に開発するベンダーのため、インターフェース仕様書

## 実装
AWSのサーバーレスAPIを簡単にdeployするために[AWS Chalice](https://aws.github.io/chalice/)というframeworkを使います。Chaliceで開発スピードも速いです。Chaliceで様々な延長機能もあります。例えば、[SDK](https://aws.github.io/chalice/topics/sdks.html)なども自動的に生成できます。これで、バックエンドがスムーズに成長できると思います。

### 構成図
<p align="center">
  <img src="simplediagram.png" width="400"/>
</p>

その他
- [接続性リクエストの流れ](availability.png)
- [コマンドリクエストの流れ](command.png)

### 条件
- AWS
  - API Gateway
  - IoT Core
  - Lambda
- Python 3.7+

### 使い方
まずはlocalでAWSのSDKやCLI Credentialsを設定してください。様々な設定仕方があるんですが、`~/.aws/config`でやるのはおすすめです。詳しくは[こちら](https://aws.github.io/chalice/quickstart.html#credentials)です。

次、Python3.7のVENVを作ってactivateします。

```
python3 -m venv venv
. /bin/activate
```

AWSのchaliceをインストールします。後、`help`でインストールしたことを確認できます。

```
pip install chalice
chalice --help
```

次、このリポジトリをクローンして、`cd`でフォルダーに入ります。

```
git clone git@github.com:Phamiliarize/IoTLite.git
cd IoTLite
```

AWSに`chalice deploy`でdeployします。

```
$ chalice deploy
Creating deployment package.
Creating IAM role: helloworld-dev
Creating lambda function: helloworld-dev
Creating Rest API
Resources deployed:
  - Lambda ARN: arn:aws:lambda:us-west-2:12345:function:helloworld-dev
  - Rest API URL: https://abcd.execute-api.us-west-2.amazonaws.com/api/
```

deployしたリージョンのIoT Coreの方で、`lightPolicy`のポリシーを登録してください。中身は`lightPolicy.json`の方です。リージョンとアカウントIDを適切に置き換えてください。それで、REST API URLを使えます。

調査が終わってから、作ったリソースが`chalice delete`で簡単に消せます。

```
$ chalice delete
Deleting Rest API: abcd4kwyl4
Deleting function aws:arn:lambda:region:123456789:helloworld-dev
Deleting IAM Role helloworld-dev
```

### 機能
- Device Onboarding
-- Register Device
--- Created Thing + Cert + Assigns dynamic policy that allows communication on channels of the thing only

- Device Status
-- List Devices (Connection Status Included)
-- Get Device (Connection Status Included)

- Device Control
-- Commands

### インターフェース仕様書


### 将来の延長
- 今回、ユーザ認証システムが顧客要件に入れていないので、実装しないですが、することになったら、Chaliceで簡単に[Cognito Userpool](https://aws.github.io/chalice/topics/authorizers.html#amazon-cognito-user-pools)を統合するできます。実装することをおすすめです。
- 新しいコマンドが自由にCOMMANDSのdictionaryに追加できます。