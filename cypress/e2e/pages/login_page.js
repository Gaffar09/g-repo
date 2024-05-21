export class LoginPage{

    email_textbox = '#email'
    password_textbox= '#password'
    login_textbox= '.flex-col > .bg-green-600'
    enterUsername(){
        cy.get(this.email_textbox).type('Admin')
    }

    enterPassword(){
        cy.get(this.password_textbox).type('admin123')
    }
    
    clickLogin(){ 
        cy.get(this.login_textbox).click()
    } 

}