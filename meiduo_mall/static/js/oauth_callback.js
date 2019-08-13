var vm = new Vue({
    el: '.register_con',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host: host,
        error_phone: false,
        error_password: false,
        error_image_code: false,
        error_sms_code: false,
        error_phone_message: '请输入正确的手机号码',
        error_password_message: '请输入8-20位的密码',
        error_image_code_message: '请填写图形验证码',
        error_sms_code_message: '请填写短信验证码',
        image_code_id: '',
        image_code_url: '',
        sms_code_tip: '获取短信验证码',
        sending_flag: false,
        password: '',
        mobile: '',
        image_code: '',
        sms_code: '',
        openid: ""
    },
    mounted: function () {
        // 向服务器获取图片验证码
        this.generate_image_code();
    },
    methods: {
        generateUUID: function () {
            var d = new Date().getTime();
            if (window.performance && typeof window.performance.now === "function") {
                d += performance.now(); //use high-precision timer if available
            }
            var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                var r = (d + Math.random() * 16) % 16 | 0;
                d = Math.floor(d / 16);
                return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
            });
            return uuid;
        },
        // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
        generate_image_code: function () {
            // 生成一个编号 : 严格一点的使用uuid保证编号唯一， 不是很严谨的情况下，也可以使用时间戳
            this.image_code_id = this.generateUUID();
            // 设置页面中图片验证码img标签的src属性
            this.image_code_url = this.host + "/image_codes/" + this.image_code_id + "/";
            console.log(this.image_code_url);
        },
        // 检查手机号
        check_phone() {
            var re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_phone_message = '您输入的手机号格式不正确';
                this.error_mobile = true;
            }
        },
        // 检查密码
        check_pwd: function () {
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },

        // 检查图片验证码
        check_image_code: function () {
            if (!this.image_code) {
                this.error_image_code_message = '请填写图片验证码';
                this.error_image_code = true;
            } else {
                this.error_image_code = false;
            }

        },

        // 发送手机短信验证码
        check_sms_code() {
            if (!this.sms_code) {
                this.error_sms_code_message = '请填写短信验证码';
                this.error_sms_code = true;
            } else {
                this.error_sms_code = false;
            }
        },
        // 发送手机短信验证码
        send_sms_code: function () {
            if (this.sending_flag == true) {
                return;
            }
            this.sending_flag = true;

            // 校验参数，保证输入框有数据填写
            if (this.error_phone == false) {
                this.check_image_code();
            }


            if (this.error_phone == true || this.error_image_code == true) {
                this.sending_flag = false;
                return;
            }

            // 向后端接口发送请求，让后端发送短信验证码
            var url = this.host + '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code + '&image_code_id=' + this.image_code_id;
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    // 表示后端发送短信成功
                    if (response.data.code == '0') {
                        // 倒计时60秒，60秒后允许用户再次点击发送短信验证码的按钮
                        var num = 60;
                        // 设置一个计时器
                        var t = setInterval(() => {
                            if (num == 1) {
                                // 如果计时器到最后, 清除计时器对象
                                clearInterval(t);
                                // 将点击获取验证码的按钮展示的文本回复成原始文本
                                this.sms_code_tip = '获取短信验证码';
                                // 将点击按钮的onclick事件函数恢复回去
                                this.sending_flag = false;
                            } else {
                                num -= 1;
                                // 展示倒计时信息
                                this.sms_code_tip = num + '秒';
                            }
                        }, 1000, 60)
                    } else {
                        if (response.data.code == '4001') {
                            this.error_image_code_message = response.data.errmsg;
                            this.error_image_code = true;
                        } else { // 4002
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true;
                        }
                        this.generate_image_code();
                        this.sending_flag = false;
                    }
                })
                .catch(error => {
                    console.log(error.response);
                    this.sending_flag = false;
                })
        },
        // 绑定openid
        on_submit() {
            this.check_pwd();
            this.check_phone();
            this.check_sms_code();

            if (this.error_password == true || this.error_mobile == true || this.error_sms_code == true) {
                // 不满足条件：禁用表单
                window.event.returnValue = false
            }
        }

        // var url = this.host + '/register/';
        // axios.post(url, {
        //     username: this.username,
        //     password: this.password,
        //     password2: this.password2,
        //     mobile: this.mobile,
        //     // 'image_code':this.image_code,
        //     sms_code: this.sms_code,
        //     allow: this.allow
        // }, {
        //     responseType: 'json'
        // })
        //     .then(response => {
        //     })
        //     .catch(error => {
        //     });
    }
});


