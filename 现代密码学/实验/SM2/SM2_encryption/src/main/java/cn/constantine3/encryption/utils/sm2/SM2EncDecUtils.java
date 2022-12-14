package cn.constantine3.encryption.utils.sm2;

import cn.constantine3.encryption.utils.Util;
import org.bouncycastle.crypto.AsymmetricCipherKeyPair;
import org.bouncycastle.crypto.params.ECPrivateKeyParameters;
import org.bouncycastle.crypto.params.ECPublicKeyParameters;
import org.bouncycastle.math.ec.ECPoint;

import java.math.BigInteger;

public class SM2EncDecUtils {

    //生成随机秘钥对
    public static SM2KeyVO generateKeyPair(){
        SM2 sm2 = SM2.Instance();
        AsymmetricCipherKeyPair key;
        while (true){
            key=sm2.ecc_key_pair_generator.generateKeyPair();
            if(((ECPrivateKeyParameters) key.getPrivate()).getD().toByteArray().length==32){
                break;
            }
        }
        ECPrivateKeyParameters ecpriv = (ECPrivateKeyParameters) key.getPrivate();
        ECPublicKeyParameters ecpub = (ECPublicKeyParameters) key.getPublic();
        BigInteger privateKey = ecpriv.getD();
        ECPoint publicKey = ecpub.getQ();
        SM2KeyVO sm2KeyVO = new SM2KeyVO();
        sm2KeyVO.setPublicKey(publicKey);
        sm2KeyVO.setPrivateKey(privateKey);
        return sm2KeyVO;
    }

    //数据加密
    public static String encrypt(byte[] publicKey, byte[] data) {
        if (publicKey == null || publicKey.length == 0)
        {
            return null;
        }

        if (data == null || data.length == 0)
        {
            return null;
        }

        byte[] source = new byte[data.length];
        System.arraycopy(data, 0, source, 0, data.length);

        Cipher cipher = new Cipher();
        SM2 sm2 = SM2.Instance();
        ECPoint userKey = sm2.ecc_curve.decodePoint(publicKey);

        ECPoint c1 = cipher.Init_enc(sm2, userKey);
        cipher.Encrypt(source);
        byte[] c3 = new byte[32];
        cipher.Dofinal(c3);

        return Util.byteToHex(c1.getEncoded()) + Util.byteToHex(c3) + Util.byteToHex(source);
    }

    //数据解密
    public static byte[] decrypt(byte[] privateKey, byte[] encryptedData) {
        if (privateKey == null || privateKey.length == 0)
        {
            return null;
        }

        if (encryptedData == null || encryptedData.length == 0)
        {
            return null;
        }
        //加密字节数组转换为十六进制的字符串 长度变为encryptedData.length * 2
        String data = Util.byteToHex(encryptedData);
        byte[] c1Bytes = Util.hexToByte(data.substring(0,130));
        int c2Len = encryptedData.length - 97;
        byte[] c3 = Util.hexToByte(data.substring(130,130 + 64));
        byte[] c2 = Util.hexToByte(data.substring(194,194 + 2 * c2Len));

        SM2 sm2 = SM2.Instance();
        BigInteger userD = new BigInteger(1, privateKey);

        //通过C1实体字节来生成ECPoint
        ECPoint c1 = sm2.ecc_curve.decodePoint(c1Bytes);
        Cipher cipher = new Cipher();
        cipher.Init_dec(userD, c1);
        cipher.Decrypt(c2);
        cipher.Dofinal(c3);

        //返回解密结果
        return c2;
    }
}
