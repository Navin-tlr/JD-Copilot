import React from "react";
import { SafeAreaView, View, ScrollView, Image, TouchableOpacity, Text, } from "react-native";
export default (props) => {
return (
<SafeAreaView 
style={{
flex: 1,
backgroundColor: "#FFFFFF",
}}>
<ScrollView  
style={{
flex: 1,
backgroundColor: "#FFFFFF",
paddingHorizontal: 20,
}}>
<Image
source = {{uri: "https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/06qqsua7_expires_30_days.png"}} 
resizeMode = {"stretch"}
style={{
width: 76,
height: 76,
marginTop: 347,
marginBottom: 286,
}}
/>
<View 
style={{
backgroundColor: "#FFFFFF",
borderRadius: 5,
paddingVertical: 11,
marginBottom: 31,
shadowColor: "#00000040",
shadowOpacity: 0.3,
shadowOffset: {
    width: 0,
    height: 0
},
shadowRadius: 6,
elevation: 6,
}}>
<TouchableOpacity 
style={{
flexDirection: "row",
alignItems: "center",
backgroundColor: "#8C57FF",
borderRadius: 2,
paddingVertical: 5,
paddingHorizontal: 9,
marginBottom: 9,
marginLeft: 12,
shadowColor: "#00000040",
shadowOpacity: 0.3,
shadowOffset: {
    width: 0,
    height: 1
},
shadowRadius: 4,
elevation: 4,
}} onPress={()=>alert('Pressed!')}>
<Image
source = {{uri: "https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/swb43i6i_expires_30_days.png"}} 
resizeMode = {"stretch"}
style={{
width: 16,
height: 16,
marginRight: 5,
}}
/>
<Text 
style={{
color: "#ECECEC",
fontSize: 10,
fontWeight: "bold",
}}>
{"RAG"}
</Text>
</TouchableOpacity>
<Text 
style={{
color: "#575353",
fontSize: 12,
marginLeft: 14,
}}>
{"Ask, search and I’ll answer...."}
</Text>
<View 
style={{
flexDirection: "row",
justifyContent: "space-between",
alignItems: "center",
marginHorizontal: 14,
}}>
<Image
source = {{uri: "https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/jp5ykuk4_expires_30_days.png"}} 
resizeMode = {"stretch"}
style={{
width: 25,
height: 25,
}}
/>
<Image
source = {{uri: "https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/xx8dfl3s_expires_30_days.png"}} 
resizeMode = {"stretch"}
style={{
width: 41,
height: 41,
}}
/>
</View>
</View>
</ScrollView>
</SafeAreaView>
)
}